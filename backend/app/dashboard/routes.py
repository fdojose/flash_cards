"""
Dashboard Routes

FastAPI routes for dashboard analytics, progress tracking, and insights.
"""
from datetime import datetime, timedelta, date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, Integer, cast, DATE
import calendar

from .models import UserStats, DatasetProgress, StudySession, WeeklyGoal, LearningInsight
from .schemas import (
    DashboardSummaryResponse, DatasetProgressResponse, StudySessionResponse,
    WeeklyGoalResponse, LearningInsightResponse, ProgressChartResponse,
    StudyHeatmapResponse, WeeklyGoalUpdate
)
from ..auth.routes import get_current_user
from ..auth.models import User
from ..sessions.models import UserElementReview, UserFieldAttempt, UserLearningSet, UserLearningSetItem
from ..datasets.models import Dataset, Element
from ..gamification.models import UserAchievement, UserStreak
from ..database import get_db
from .ranking_service import RankingService
from ..admin.models import SystemConfig

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall dashboard summary for the user"""
    
    # Get or create user stats
    user_stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
    if not user_stats:
        user_stats = await _calculate_user_stats(db, current_user.id)
    
    # Get streak information (handle missing table gracefully)
    current_streak = 0
    max_streak = 0
    try:
        streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
        current_streak = streak.current_streak if streak else 0
        max_streak = streak.max_streak if streak else 0
    except Exception:
        # Handle missing UserStreak table
        current_streak = 0
        max_streak = 0
    
    # Get recent achievements (handle missing table gracefully)
    recent_badges = []
    try:
        recent_badges = db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id
        ).order_by(desc(UserAchievement.date_awarded)).limit(3).all()
    except Exception:
        # Handle missing UserAchievement table
        recent_badges = []
    
    # Get cards due today
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    cards_due_today = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.next_due >= datetime.combine(today, datetime.min.time()),
            UserElementReview.next_due < datetime.combine(tomorrow, datetime.min.time()),
            UserElementReview.status.not_in(["isolation_mastered", "integration_confirmed"])
        )
    ).scalar() or 0
    
    # Get weekly goal progress (handle missing table gracefully)
    weekly_goal_progress = {"current": 0, "target": 0, "percentage": 0}
    try:
        week_start = date.today() - timedelta(days=date.today().weekday())
        weekly_goal = db.query(WeeklyGoal).filter(
            and_(
                WeeklyGoal.user_id == current_user.id,
                WeeklyGoal.week_start_date >= datetime.combine(week_start, datetime.min.time())
            )
        ).first()
        if weekly_goal:
            weekly_goal_progress = {
                "current": weekly_goal.current_progress,
                "target": weekly_goal.target_reviews,
                "percentage": min(100, (weekly_goal.current_progress / weekly_goal.target_reviews) * 100) if weekly_goal.target_reviews > 0 else 0
            }
    except Exception:
        # Handle missing WeeklyGoal table
        weekly_goal_progress = {"current": 0, "target": 0, "percentage": 0}
    
    return DashboardSummaryResponse(
        total_elements_mastered=user_stats.total_elements_mastered,
        total_reviews=user_stats.total_reviews,
        overall_accuracy=user_stats.overall_accuracy,
        current_streak=current_streak,
        max_streak=max_streak,
        cards_due_today=cards_due_today,
        active_datasets=user_stats.active_datasets,
        recent_badges=[badge.badge_name for badge in recent_badges],
        weekly_goal_progress={
            "sessions_target": weekly_goal.target_sessions_per_week if weekly_goal else 5,
            "sessions_completed": weekly_goal.sessions_completed if weekly_goal else 0,
            "minutes_target": weekly_goal.target_minutes_per_week if weekly_goal else 150,
            "minutes_completed": weekly_goal.minutes_studied if weekly_goal else 0
        } if weekly_goal else None
    )


@router.get("/datasets", response_model=List[DatasetProgressResponse])
async def get_dataset_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress for all datasets the user has studied"""
    
    # Update dataset progress before returning data
    await _update_dataset_progress(db, current_user.id)
    
    progress_records = db.query(DatasetProgress, Dataset.name).join(
        Dataset, DatasetProgress.dataset_id == Dataset.id
    ).filter(
        DatasetProgress.user_id == current_user.id
    ).all()

    results = []
    for progress, dataset_name in progress_records:
        # Get the learning set ID for this dataset
        learning_set = db.query(UserLearningSet).filter(
            UserLearningSet.user_id == current_user.id,
            UserLearningSet.dataset_id == progress.dataset_id
        ).first()
        
        # Calculate failed elements for this dataset using UserFieldAttempt
        failed_elements_count = db.query(func.count(func.distinct(Element.id))).join(
            UserFieldAttempt, Element.id == UserFieldAttempt.element_id
        ).filter(
            Element.dataset_id == progress.dataset_id,
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.is_correct == False  # Only failed responses
        ).scalar() or 0
        
        results.append(DatasetProgressResponse(
            dataset_id=progress.dataset_id,
            dataset_name=dataset_name,
            elements_in_dataset=progress.elements_in_dataset,
            elements_seen=progress.elements_seen,
            elements_mastered=progress.elements_mastered,
            failed_elements=failed_elements_count,
            current_stage=progress.current_stage,
            accuracy_rate=progress.accuracy_rate,
            completion_percentage=progress.completion_percentage,
            status=progress.status,
            started_at=progress.started_at,
            last_studied=progress.last_studied,
            learning_set_id=str(learning_set.id) if learning_set else None
        ))
    
    return results


@router.post("/datasets/{dataset_id}/reset")
async def reset_dataset_progress(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset all learning progress for a specific dataset"""
    
    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Delete all user element reviews for this dataset
        user_reviews = db.query(UserElementReview).join(Element).filter(
            and_(
                UserElementReview.user_id == current_user.id,
                Element.dataset_id == dataset_id
            )
        ).all()
        
        for review in user_reviews:
            db.delete(review)
        
        # Delete all field attempts for this dataset
        field_attempts = db.query(UserFieldAttempt).join(Element).filter(
            and_(
                UserFieldAttempt.user_id == current_user.id,
                Element.dataset_id == dataset_id
            )
        ).all()
        
        for attempt in field_attempts:
            db.delete(attempt)
        
        # Delete learning set and items for this dataset
        learning_set = db.query(UserLearningSet).filter(
            and_(
                UserLearningSet.user_id == current_user.id,
                UserLearningSet.dataset_id == dataset_id
            )
        ).first()
        
        if learning_set:
            # Delete learning set items first
            db.query(UserLearningSetItem).filter(
                UserLearningSetItem.learning_set_id == learning_set.id
            ).delete()
            
            # Delete the learning set
            db.delete(learning_set)
        
        # Delete dataset progress record
        dataset_progress = db.query(DatasetProgress).filter(
            and_(
                DatasetProgress.user_id == current_user.id,
                DatasetProgress.dataset_id == dataset_id
            )
        ).first()
        
        if dataset_progress:
            db.delete(dataset_progress)
        
        # Commit all changes
        db.commit()
        
        return {
            "message": "Dataset progress reset successfully",
            "dataset_id": str(dataset_id),
            "dataset_name": dataset.name
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reset dataset progress: {str(e)}"
        )


@router.get("/chart/progress", response_model=ProgressChartResponse)
async def get_progress_chart(
    days: int = Query(30, description="Number of days to include in chart"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get progress chart data for the specified number of days"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily review counts
    daily_reviews = db.query(
        func.date(UserFieldAttempt.attempted_at).label('date'),
        func.count(UserFieldAttempt.id).label('reviews'),
        func.avg(func.cast(UserFieldAttempt.is_correct, Integer)).label('accuracy')
    ).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.attempted_at >= start_date
        )
    ).group_by(func.date(UserFieldAttempt.attempted_at)).all()
    
    # Get cumulative mastered count
    mastery_progression = db.query(
        func.date(UserElementReview.updated_at).label('date'),
        func.count(UserElementReview.id).label('mastered_count')
    ).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"]),
            UserElementReview.updated_at >= start_date
        )
    ).group_by(func.date(UserElementReview.updated_at)).all()
    
    # Format data for chart
    chart_data = {
        "dates": [],
        "daily_reviews": [],
        "daily_accuracy": [],
        "cumulative_mastered": []
    }
    
    current_mastered = 0
    for i in range(days):
        chart_date = (datetime.utcnow() - timedelta(days=days-i-1)).date()
        chart_data["dates"].append(chart_date.isoformat())
        
        # Find review data for this date
        day_reviews = next((r for r in daily_reviews if r.date == chart_date), None)
        chart_data["daily_reviews"].append(day_reviews.reviews if day_reviews else 0)
        chart_data["daily_accuracy"].append(
            round(day_reviews.accuracy * 100, 1) if day_reviews and day_reviews.accuracy else 0
        )
        
        # Find mastery data for this date
        day_mastery = next((m for m in mastery_progression if m.date == chart_date), None)
        if day_mastery:
            current_mastered += day_mastery.mastered_count
        chart_data["cumulative_mastered"].append(current_mastered)
    
    return ProgressChartResponse(**chart_data)


@router.get("/heatmap", response_model=StudyHeatmapResponse)
async def get_study_heatmap(
    year: int = Query(None, description="Year for heatmap (default: current year)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get study activity heatmap for the specified year"""
    
    if not year:
        year = datetime.utcnow().year
    
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    # Get daily activity counts
    daily_activity = db.query(
        func.date(UserFieldAttempt.attempted_at).label('date'),
        func.count(UserFieldAttempt.id).label('activity_count')
    ).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.attempted_at >= start_date,
            UserFieldAttempt.attempted_at < end_date
        )
    ).group_by(func.date(UserFieldAttempt.attempted_at)).all()
    
    # Create activity map
    activity_map = {activity.date.isoformat(): activity.activity_count for activity in daily_activity}
    
    return StudyHeatmapResponse(
        year=year,
        activity_data=activity_map,
        total_active_days=len(daily_activity),
        max_daily_activity=max([a.activity_count for a in daily_activity]) if daily_activity else 0
    )


@router.get("/goals", response_model=WeeklyGoalResponse)
async def get_weekly_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current weekly goals and progress"""
    
    # Get current week's goal
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_goal = db.query(WeeklyGoal).filter(
        and_(
            WeeklyGoal.user_id == current_user.id,
            WeeklyGoal.week_start_date >= datetime.combine(week_start, datetime.min.time())
        )
    ).first()
    
    if not weekly_goal:
        # Create default weekly goal
        weekly_goal = WeeklyGoal(
            user_id=current_user.id,
            week_start_date=datetime.combine(week_start, datetime.min.time())
        )
        db.add(weekly_goal)
        db.commit()
        db.refresh(weekly_goal)
    
    return WeeklyGoalResponse.from_orm(weekly_goal)


@router.put("/goals", response_model=WeeklyGoalResponse)
async def update_weekly_goals(
    updates: WeeklyGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update weekly learning goals"""
    
    week_start = date.today() - timedelta(days=date.today().weekday())
    weekly_goal = db.query(WeeklyGoal).filter(
        and_(
            WeeklyGoal.user_id == current_user.id,
            WeeklyGoal.week_start_date >= datetime.combine(week_start, datetime.min.time())
        )
    ).first()
    
    if not weekly_goal:
        weekly_goal = WeeklyGoal(
            user_id=current_user.id,
            week_start_date=datetime.combine(week_start, datetime.min.time())
        )
        db.add(weekly_goal)
    
    # Update goals
    if updates.target_sessions_per_week is not None:
        weekly_goal.target_sessions_per_week = updates.target_sessions_per_week
    if updates.target_minutes_per_week is not None:
        weekly_goal.target_minutes_per_week = updates.target_minutes_per_week
    if updates.target_cards_per_week is not None:
        weekly_goal.target_cards_per_week = updates.target_cards_per_week
    
    db.commit()
    db.refresh(weekly_goal)
    
    return WeeklyGoalResponse.from_orm(weekly_goal)


@router.get("/insights", response_model=List[LearningInsightResponse])
async def get_learning_insights(
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-generated learning insights for the user"""
    
    insights = db.query(LearningInsight).filter(
        and_(
            LearningInsight.user_id == current_user.id,
            LearningInsight.expires_at > datetime.utcnow()
        )
    ).order_by(
        desc(LearningInsight.priority),
        desc(LearningInsight.confidence_score)
    ).limit(limit).all()
    
    return [LearningInsightResponse.from_orm(insight) for insight in insights]


@router.post("/refresh-stats")
async def refresh_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually refresh cached user statistics"""
    
    user_stats = await _calculate_user_stats(db, current_user.id)
    await _update_dataset_progress(db, current_user.id)
    
    return {"message": "Statistics refreshed successfully"}


async def _calculate_user_stats(db: Session, user_id: str) -> UserStats:
    """Calculate and cache user statistics"""
    
    # Get existing stats or create new
    user_stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
    if not user_stats:
        user_stats = UserStats(user_id=user_id)
        db.add(user_stats)
    
    # Calculate metrics
    total_reviews = db.query(func.count(UserElementReview.id)).filter(
        UserElementReview.user_id == user_id
    ).scalar() or 0
    
    mastered_count = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == user_id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"])
        )
    ).scalar() or 0
    
    total_attempts = db.query(func.count(UserFieldAttempt.id)).filter(
        UserFieldAttempt.user_id == user_id
    ).scalar() or 0
    
    correct_attempts = db.query(func.count(UserFieldAttempt.id)).filter(
        and_(
            UserFieldAttempt.user_id == user_id,
            UserFieldAttempt.is_correct == True
        )
    ).scalar() or 0
    
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    active_datasets = db.query(func.count(UserLearningSet.id)).filter(
        and_(
            UserLearningSet.user_id == user_id,
            UserLearningSet.status == "active"
        )
    ).scalar() or 0
    
    # Fetch streak data
    streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
    current_streak = streak.current_streak if streak else 0
    max_streak = streak.max_streak if streak else 0

    # Update stats
    user_stats.total_elements_seen = total_reviews
    user_stats.total_elements_mastered = mastered_count
    user_stats.total_reviews = total_attempts
    user_stats.overall_accuracy = accuracy
    user_stats.active_datasets = active_datasets
    user_stats.mastery_rate = (mastered_count / total_reviews * 100) if total_reviews > 0 else 0
    user_stats.current_streak = current_streak
    user_stats.max_streak = max_streak
    user_stats.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(user_stats)
    
    return user_stats


async def _update_dataset_progress(db: Session, user_id: str):
    """Update progress tracking for all user's datasets"""
    
    # Get all unique dataset IDs the user has interacted with
    # Method 1: From learning sets
    learning_set_datasets = db.query(UserLearningSet.dataset_id).filter(
        UserLearningSet.user_id == user_id
    ).distinct().all()
    
    # Method 2: From element reviews (join Element to get dataset_id)
    review_datasets = db.query(Element.dataset_id).join(
        UserElementReview, UserElementReview.element_id == Element.id
    ).filter(
        UserElementReview.user_id == user_id
    ).distinct().all()
    
    # Combine both lists and get unique dataset IDs
    all_dataset_ids = set()
    for (dataset_id,) in learning_set_datasets:
        all_dataset_ids.add(dataset_id)
    for (dataset_id,) in review_datasets:
        all_dataset_ids.add(dataset_id)
    
    for dataset_id in all_dataset_ids:
        progress = db.query(DatasetProgress).filter(
            and_(
                DatasetProgress.user_id == user_id,
                DatasetProgress.dataset_id == dataset_id
            )
        ).first()
        
        if not progress:
            progress = DatasetProgress(
                user_id=user_id,
                dataset_id=dataset_id
            )
            db.add(progress)
        
        # Calculate progress metrics
        # Get total elements in the dataset
        total_elements = db.query(func.count(Element.id)).filter(
            Element.dataset_id == dataset_id
        ).scalar() or 0
        
        # Get elements the user has interacted with
        user_reviews = db.query(UserElementReview).join(Element).filter(
            and_(
                UserElementReview.user_id == user_id,
                Element.dataset_id == dataset_id
            )
        ).all()
        
        elements_seen = len(user_reviews)
        elements_mastered = len([r for r in user_reviews if r.status in ("isolation_mastered", "integration_confirmed")])
        
        # Calculate accuracy for this dataset
        attempts = db.query(UserFieldAttempt).join(Element).filter(
            and_(
                UserFieldAttempt.user_id == user_id,
                Element.dataset_id == dataset_id
            )
        ).all()
        
        if attempts:
            correct_attempts = len([a for a in attempts if a.is_correct])
            accuracy_rate = (correct_attempts / len(attempts)) * 100
            
            # Calculate average response time
            response_times = [a.response_time_ms for a in attempts if a.response_time_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        else:
            accuracy_rate = 0
            avg_response_time = 0
        
        # Calculate completion percentage
        completion_percentage = (elements_mastered / total_elements) if total_elements > 0 else 0
        
        # Get current stage from learning set if it exists
        learning_set = db.query(UserLearningSet).filter(
            and_(
                UserLearningSet.user_id == user_id,
                UserLearningSet.dataset_id == dataset_id
            )
        ).first()
        
        # Derive stage from batch progression (mastered_up_to / batch_size).
        # learning_set.stage is only updated by the legacy advance-stage endpoint
        # and stays at 1 in the batch-based flow, so we compute it directly.
        if learning_set and learning_set.batch_size and learning_set.mastered_up_to:
            current_stage = max(1, learning_set.mastered_up_to // learning_set.batch_size)
        elif learning_set:
            current_stage = learning_set.stage
        else:
            current_stage = 1
        status = learning_set.status if learning_set else ("completed" if elements_mastered == total_elements and total_elements > 0 else "active")
        
        # Update progress record
        progress.elements_in_dataset = total_elements
        progress.elements_seen = elements_seen
        progress.elements_mastered = elements_mastered
        progress.current_stage = current_stage
        progress.accuracy_rate = accuracy_rate
        progress.avg_response_time = avg_response_time
        progress.completion_percentage = completion_percentage
        progress.status = status
        progress.last_studied = datetime.utcnow()
        
        # Set completed_at if fully mastered
        if elements_mastered == total_elements and total_elements > 0:
            progress.status = "completed"
            if not progress.completed_at:
                progress.completed_at = datetime.utcnow()
        
    db.commit()


@router.get("/progress")
async def get_user_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user progress data"""
    # Get recent activity by grouping field attempts by day
    from sqlalchemy import DATE, cast
    
    recent_activity = db.query(
        cast(UserFieldAttempt.attempted_at, DATE).label('date'),
        func.count(UserFieldAttempt.id).label('total_reviews'),
        func.count(func.nullif(UserFieldAttempt.is_correct, False)).label('correct_reviews')
    ).filter(
        UserFieldAttempt.user_id == current_user.id
    ).group_by(
        cast(UserFieldAttempt.attempted_at, DATE)
    ).order_by(
        cast(UserFieldAttempt.attempted_at, DATE).desc()
    ).limit(7).all()
    
    sessions_data = []
    for activity in recent_activity:
        # Get a sample element from that day to show dataset name
        sample_attempt = db.query(UserFieldAttempt).filter(
            and_(
                UserFieldAttempt.user_id == current_user.id,
                cast(UserFieldAttempt.attempted_at, DATE) == activity.date
            )
        ).first()
        
        if sample_attempt:
            # Get dataset name from the element
            element = db.query(Element).filter(Element.id == sample_attempt.element_id).first()
            if element:
                dataset = db.query(Dataset).filter(Dataset.id == element.dataset_id).first()
                dataset_name = dataset.name if dataset else "Unknown Dataset"
            else:
                dataset_name = "Unknown Dataset"
        else:
            dataset_name = "Unknown Dataset"
        
        sessions_data.append({
            "dataset": dataset_name,
            "correct": activity.correct_reviews,
            "total": activity.total_reviews,
            "time": activity.date.strftime("%Y-%m-%d")
        })
    
    return {
        "recent_sessions": sessions_data
    }


@router.get("/progress-history")
async def get_progress_history(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily progress history for the specified number of days"""
    from sqlalchemy import DATE, cast
    from datetime import datetime, timedelta
    
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily activity
    daily_activity = db.query(
        cast(UserFieldAttempt.attempted_at, DATE).label('date'),
        func.count(UserFieldAttempt.id).label('reviews'),
        (func.sum(func.cast(UserFieldAttempt.is_correct, Integer)) / func.count(UserFieldAttempt.id)).label('accuracy')
    ).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            cast(UserFieldAttempt.attempted_at, DATE) >= start_date,
            cast(UserFieldAttempt.attempted_at, DATE) <= end_date
        )
    ).group_by(
        cast(UserFieldAttempt.attempted_at, DATE)
    ).order_by(
        cast(UserFieldAttempt.attempted_at, DATE).asc()
    ).all()
    
    # Convert to the format expected by frontend
    history_data = []
    for activity in daily_activity:
        history_data.append({
            "date": activity.date.isoformat(),
            "reviews": activity.reviews,
            "accuracy": round((activity.accuracy or 0) * 100, 1)  # Convert to percentage
        })
    
    return history_data


@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics"""
    # Get total mastered elements
    mastered_count = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.status.in_(["isolation_mastered", "integration_confirmed"])
        )
    ).scalar() or 0
    
    # Get total reviews
    total_reviews = db.query(func.count(UserFieldAttempt.id)).filter(
        UserFieldAttempt.user_id == current_user.id
    ).scalar() or 0
    
    # Get accuracy rate
    if total_reviews > 0:
        correct_reviews = db.query(func.count(UserFieldAttempt.id)).filter(
            and_(
                UserFieldAttempt.user_id == current_user.id,
                UserFieldAttempt.is_correct == True
            )
        ).scalar() or 0
        accuracy_rate = (correct_reviews / total_reviews) * 100
    else:
        accuracy_rate = 0
    
    # Get streak
    streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    current_streak = streak.current_streak if streak else 0
    
    return {
        "mastered_count": mastered_count,
        "total_reviews": total_reviews,
        "accuracy_rate": accuracy_rate,
        "current_streak": current_streak
    }


@router.get("/achievements")
async def get_user_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user achievements"""
    achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id
    ).order_by(desc(UserAchievement.date_awarded)).all()
    
    achievements_data = []
    for achievement in achievements:
        achievements_data.append({
            "id": achievement.id,
            "title": achievement.achievement_title,
            "description": achievement.achievement_description,
            "badge_emoji": achievement.badge_emoji,
            "date_awarded": achievement.date_awarded.strftime("%Y-%m-%d")
        })
    
    return achievements_data


# ========== GAMIFICATION RANKING ENDPOINTS ==========

@router.get("/rankings/cards-answered")
async def get_cards_answered_ranking(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top users by total cards answered"""
    ranking_service = RankingService(db)
    return ranking_service.get_cards_answered_ranking(limit)


@router.get("/rankings/accuracy")
async def get_accuracy_ranking(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    min_cards: Optional[int] = Query(None, ge=1, description="Minimum cards answered (uses config default if not provided)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top users by accuracy (with minimum cards threshold from admin config)"""
    ranking_service = RankingService(db)
    return ranking_service.get_accuracy_ranking(limit, min_cards)


@router.get("/rankings/speed")
async def get_speed_ranking(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    min_cards: Optional[int] = Query(None, ge=1, description="Minimum cards for speed ranking (uses config default if not provided)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top users by speed score (volume-weighted, min cards from admin config)"""
    ranking_service = RankingService(db)
    return ranking_service.get_speed_ranking(limit, min_cards)


@router.get("/rankings/overall")
async def get_overall_ranking(
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top users by combined overall score"""
    ranking_service = RankingService(db)
    return ranking_service.get_overall_ranking(limit)


@router.post("/rankings/refresh/{user_id}")
async def refresh_user_statistics(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate and update user statistics (admin or self only)"""
    # Allow users to refresh their own stats, or admin to refresh any
    if str(current_user.id) != user_id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only refresh your own statistics"
        )
    
    ranking_service = RankingService(db)
    try:
        updated_stats = ranking_service.calculate_user_statistics(user_id)
        return {
            "success": True,
            "message": "User statistics refreshed",
            "updated_at": updated_stats.last_activity_date,
            "stats": {
                "total_cards_answered": updated_stats.total_cards_answered,
                "accuracy_percentage": updated_stats.accuracy_percentage,
                "speed_score": updated_stats.speed_score,
                "overall_score": updated_stats.overall_score
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh statistics: {str(e)}"
        )
