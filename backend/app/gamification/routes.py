"""
Gamification Routes

FastAPI routes for badges, streaks, and leaderboards.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func

from .models import UserAchievement, UserStreak, LeaderboardScore, BadgeDefinition
from .schemas import (
    BadgeResponse, StreakResponse, LeaderboardResponse, 
    LeaderboardEntry, BadgeCreateRequest
)
from ..auth.routes import get_current_user, get_admin_user
from ..auth.models import User
from ..sessions.models import UserElementReview
from ..database import get_db

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/badges", response_model=List[BadgeResponse])
async def get_user_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all badges earned by the current user"""
    badges = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id
    ).order_by(desc(UserAchievement.date_awarded)).all()
    
    return [BadgeResponse.from_orm(badge) for badge in badges]


@router.get("/streak", response_model=StreakResponse)
async def get_user_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's streak information"""
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    
    if not streak:
        # Create initial streak record
        streak = UserStreak(
            user_id=current_user.id,
            current_streak=0,
            max_streak=0,
            last_activity=None
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)
    
    return StreakResponse.from_orm(streak)


@router.post("/streak/update")
async def update_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's streak based on today's activity"""
    today = date.today()
    
    streak = db.query(UserStreak).filter(
        UserStreak.user_id == current_user.id
    ).first()
    
    if not streak:
        streak = UserStreak(
            user_id=current_user.id,
            current_streak=1,
            max_streak=1,
            last_activity=datetime.now()
        )
        db.add(streak)
    else:
        last_activity_date = streak.last_activity.date() if streak.last_activity else None
        
        if last_activity_date == today:
            # Already updated today
            return {"message": "Streak already updated today", "current_streak": streak.current_streak}
        elif last_activity_date == today - timedelta(days=1):
            # Consecutive day - increment streak
            streak.current_streak += 1
            streak.max_streak = max(streak.max_streak, streak.current_streak)
        else:
            # Streak broken - reset
            streak.current_streak = 1
        
        streak.last_activity = datetime.now()
        streak.updated_at = datetime.now()
    
    db.commit()
    
    # Check for streak badges
    await _check_streak_badges(db, current_user.id, streak.current_streak)
    
    return {
        "message": "Streak updated",
        "current_streak": streak.current_streak,
        "max_streak": streak.max_streak
    }


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    score_type: str = Query(..., description="Type of leaderboard (mastered, streak, sessions, accuracy)"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset"),
    period: str = Query("all_time", description="Time period (daily, weekly, monthly, all_time)"),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get leaderboard for a specific metric"""
    query = db.query(LeaderboardScore, User.name).join(
        User, LeaderboardScore.user_id == User.id
    ).filter(
        and_(
            LeaderboardScore.score_type == score_type,
            LeaderboardScore.period == period
        )
    )
    
    if dataset_id:
        query = query.filter(LeaderboardScore.dataset_id == dataset_id)
    
    results = query.order_by(desc(LeaderboardScore.value)).limit(limit).all()
    
    entries = [
        LeaderboardEntry(
            rank=i + 1,
            user_id=score.user_id,
            user_name=name,
            value=score.value,
            is_current_user=(score.user_id == current_user.id)
        )
        for i, (score, name) in enumerate(results)
    ]
    
    return LeaderboardResponse(
        score_type=score_type,
        period=period,
        dataset_id=dataset_id,
        entries=entries
    )


@router.post("/badges/award")
async def award_badge(
    request: BadgeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Manually award a badge to a user (admin only)"""
    # Check if user already has this badge
    existing = db.query(UserAchievement).filter(
        and_(
            UserAchievement.user_id == request.user_id,
            UserAchievement.achievement_title == request.badge_name
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this badge"
        )

    badge = UserAchievement(
        user_id=request.user_id,
        achievement_title=request.badge_name,
        achievement_description=request.description,
        badge_emoji=request.icon
    )
    
    db.add(badge)
    db.commit()
    db.refresh(badge)
    
    return BadgeResponse.from_orm(badge)


@router.post("/scores/update")
async def update_leaderboard_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update leaderboard scores for the current user"""
    # Calculate mastered elements
    mastered_count = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.status == "mastered"
        )
    ).scalar() or 0
    
    # Update mastered score
    await _update_score(db, current_user.id, "mastered", mastered_count)
    
    # Update streak score
    streak = db.query(UserStreak).filter(UserStreak.user_id == current_user.id).first()
    if streak:
        await _update_score(db, current_user.id, "streak", streak.max_streak)
    
    db.commit()
    
    return {"message": "Scores updated successfully"}


async def _update_score(db: Session, user_id: str, score_type: str, value: int, dataset_id: str = None):
    """Helper function to update a leaderboard score across all time periods"""
    for period in ("daily", "weekly", "monthly", "all_time"):
        score = db.query(LeaderboardScore).filter(
            and_(
                LeaderboardScore.user_id == user_id,
                LeaderboardScore.score_type == score_type,
                LeaderboardScore.dataset_id == dataset_id,
                LeaderboardScore.period == period,
            )
        ).first()

        if score:
            score.value = value
            score.updated_at = datetime.now()
        else:
            db.add(LeaderboardScore(
                user_id=user_id,
                dataset_id=dataset_id,
                score_type=score_type,
                value=value,
                period=period,
            ))


async def _check_streak_badges(db: Session, user_id: str, current_streak: int):
    """Check and award streak-based badges"""
    badge_thresholds = {
        "First Steps": 1,
        "Getting Warmed Up": 3,
        "On Fire": 7,
        "Unstoppable": 14,
        "Legend": 30
    }
    
    for badge_name, threshold in badge_thresholds.items():
        if current_streak >= threshold:
            existing = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_title == badge_name
                )
            ).first()

            if not existing:
                badge = UserAchievement(
                    user_id=user_id,
                    achievement_title=badge_name,
                    achievement_description=f"Maintained a {threshold}-day learning streak",
                    badge_emoji="🔥"
                )
                db.add(badge)


async def check_mastery_badges(db: Session, user_id: str):
    """Check and award mastery-based badges (called from sessions module)"""
    mastered_count = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == user_id,
            UserElementReview.status == "mastered"
        )
    ).scalar() or 0
    
    badge_thresholds = {
        "First Mastery": 1,
        "Quick Learner": 10,
        "Knowledge Seeker": 25,
        "Expert": 50,
        "Master": 100
    }
    
    for badge_name, threshold in badge_thresholds.items():
        if mastered_count >= threshold:
            existing = db.query(UserAchievement).filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_title == badge_name
                )
            ).first()

            if not existing:
                badge = UserAchievement(
                    user_id=user_id,
                    achievement_title=badge_name,
                    achievement_description=f"Mastered {threshold} elements",
                    badge_emoji="🏆"
                )
                db.add(badge)
