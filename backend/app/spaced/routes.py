"""
Spaced Repetition Routes

FastAPI routes for advanced spaced repetition features and analytics.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .models import SpacedRepetitionConfig, ReviewSession, CardDifficulty, OptimalSchedule
from .schemas import (
    SpacedConfigResponse, SpacedConfigUpdate, ReviewSessionResponse,
    CardDifficultyResponse, OptimalScheduleResponse, SpacedAnalyticsResponse
)
from .algorithms import SM2Algorithm, calculate_card_difficulty
from ..auth.routes import get_current_user
from ..auth.models import User
from ..sessions.models import UserElementReview, UserFieldAttempt
from ..database import get_db

router = APIRouter(prefix="/spaced", tags=["spaced-repetition"])


@router.get("/config", response_model=SpacedConfigResponse)
async def get_spaced_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's spaced repetition configuration"""
    config = db.query(SpacedRepetitionConfig).filter(
        SpacedRepetitionConfig.user_id == current_user.id
    ).first()
    
    if not config:
        # Create default configuration
        config = SpacedRepetitionConfig(user_id=current_user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return SpacedConfigResponse.from_orm(config)


@router.put("/config", response_model=SpacedConfigResponse)
async def update_spaced_config(
    updates: SpacedConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's spaced repetition configuration"""
    config = db.query(SpacedRepetitionConfig).filter(
        SpacedRepetitionConfig.user_id == current_user.id
    ).first()
    
    if not config:
        config = SpacedRepetitionConfig(user_id=current_user.id)
        db.add(config)
    
    # Update fields that were provided
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    
    return SpacedConfigResponse.from_orm(config)


@router.get("/analytics", response_model=SpacedAnalyticsResponse)
async def get_spaced_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get spaced repetition analytics for the user"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get review statistics
    reviews = db.query(UserElementReview).filter(
        and_(
            UserElementReview.user_id == current_user.id,
            UserElementReview.last_reviewed >= cutoff_date
        )
    ).all()
    
    # Get attempt statistics
    attempts = db.query(UserFieldAttempt).filter(
        and_(
            UserFieldAttempt.user_id == current_user.id,
            UserFieldAttempt.attempted_at >= cutoff_date
        )
    ).all()
    
    # Calculate metrics
    total_reviews = len(reviews)
    total_attempts = len(attempts)
    correct_attempts = len([a for a in attempts if a.is_correct])
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Cards by status
    mastered_count = len([r for r in reviews if r.status in ("isolation_mastered", "integration_confirmed")])
    learning_count = len([r for r in reviews if r.status == "learning"])
    due_count = len([r for r in reviews if r.next_due and r.next_due <= datetime.utcnow()])
    
    # Average ease factor
    avg_ease = sum(r.ease_factor for r in reviews if r.ease_factor) / len(reviews) if reviews else 250
    avg_ease_factor = avg_ease / 100.0
    
    # Retention rate (approximate)
    recent_correct = len([a for a in attempts[-100:] if a.is_correct]) if attempts else 0
    retention_rate = (recent_correct / min(100, len(attempts)) * 100) if attempts else 0
    
    return SpacedAnalyticsResponse(
        total_reviews=total_reviews,
        total_attempts=total_attempts,
        accuracy_percentage=round(accuracy, 1),
        mastered_cards=mastered_count,
        learning_cards=learning_count,
        due_cards=due_count,
        average_ease_factor=round(avg_ease_factor, 2),
        retention_rate=round(retention_rate, 1),
        days_analyzed=days
    )


@router.get("/difficult-cards", response_model=List[CardDifficultyResponse])
async def get_difficult_cards(
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the most difficult cards for the user"""
    difficulties = db.query(CardDifficulty).filter(
        CardDifficulty.user_id == current_user.id
    ).order_by(CardDifficulty.difficulty_score.desc()).limit(limit).all()
    
    return [CardDifficultyResponse.from_orm(d) for d in difficulties]


@router.get("/optimal-schedule", response_model=OptimalScheduleResponse)
async def get_optimal_schedule(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get optimal review schedule for the user"""
    schedule = db.query(OptimalSchedule).filter(
        OptimalSchedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        # Calculate optimal schedule
        schedule = await _calculate_optimal_schedule(db, current_user.id)
    elif schedule.updated_at < datetime.utcnow() - timedelta(hours=24):
        # Recalculate if older than 24 hours
        schedule = await _calculate_optimal_schedule(db, current_user.id)
    
    return OptimalScheduleResponse.from_orm(schedule)


@router.post("/recalculate-intervals")
async def recalculate_intervals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recalculate spaced repetition intervals using advanced algorithm"""
    config = db.query(SpacedRepetitionConfig).filter(
        SpacedRepetitionConfig.user_id == current_user.id
    ).first()
    
    if not config:
        config = SpacedRepetitionConfig(user_id=current_user.id)
        db.add(config)
        db.commit()
    
    # Get all user reviews
    reviews = db.query(UserElementReview).filter(
        UserElementReview.user_id == current_user.id
    ).all()
    
    # Initialize algorithm
    algorithm = SM2Algorithm(config)
    updated_count = 0
    
    for review in reviews:
        if review.last_reviewed:
            # Recalculate using SM-2
            new_interval, new_ease = algorithm.calculate_next_interval(
                review.ease_factor / 100.0,  # Convert back to float
                review.success_streak,
                review.review_count > 0
            )
            
            review.interval_days = new_interval
            review.ease_factor = int(new_ease * 100)  # Store as integer
            review.next_due = review.last_reviewed + timedelta(days=new_interval)
            updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Recalculated intervals for {updated_count} cards",
        "algorithm": config.algorithm
    }


@router.post("/sessions/{session_id}/end")
async def end_review_session(
    session_id: str,
    cards_reviewed: int,
    cards_correct: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a review session and update analytics"""
    session = db.query(ReviewSession).filter(
        and_(
            ReviewSession.id == session_id,
            ReviewSession.user_id == current_user.id
        )
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review session not found"
        )
    
    # Update session
    session.ended_at = datetime.utcnow()
    session.cards_reviewed = cards_reviewed
    session.cards_correct = cards_correct
    session.total_time_ms = int((session.ended_at - session.started_at).total_seconds() * 1000)
    
    db.commit()
    
    # Update card difficulties based on recent attempts
    await _update_card_difficulties(db, current_user.id)
    
    return {"message": "Session ended successfully", "session_id": session_id}


async def _calculate_optimal_schedule(db: Session, user_id: str) -> OptimalSchedule:
    """Calculate optimal review schedule for a user"""
    # Get due cards for next 7 and 30 days
    now = datetime.utcnow()
    week_from_now = now + timedelta(days=7)
    month_from_now = now + timedelta(days=30)
    
    next_7_days = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == user_id,
            UserElementReview.next_due <= week_from_now,
            UserElementReview.next_due > now
        )
    ).scalar() or 0
    
    next_30_days = db.query(func.count(UserElementReview.id)).filter(
        and_(
            UserElementReview.user_id == user_id,
            UserElementReview.next_due <= month_from_now,
            UserElementReview.next_due > now
        )
    ).scalar() or 0
    
    # Calculate optimal session length based on review load
    optimal_length = min(max(next_7_days * 2, 10), 45)  # 10-45 minutes
    
    # Update or create schedule
    schedule = db.query(OptimalSchedule).filter(
        OptimalSchedule.user_id == user_id
    ).first()
    
    if not schedule:
        schedule = OptimalSchedule(user_id=user_id)
        db.add(schedule)
    
    schedule.next_7_days_count = next_7_days
    schedule.next_30_days_count = next_30_days
    schedule.optimal_session_length = optimal_length
    schedule.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(schedule)
    
    return schedule


async def _update_card_difficulties(db: Session, user_id: str):
    """Update card difficulty scores based on recent performance"""
    # Get recent attempts (last 30 days)
    cutoff = datetime.utcnow() - timedelta(days=30)
    
    attempts = db.query(UserFieldAttempt).filter(
        and_(
            UserFieldAttempt.user_id == user_id,
            UserFieldAttempt.attempted_at >= cutoff
        )
    ).all()
    
    # Group by element_id
    element_attempts = {}
    for attempt in attempts:
        if attempt.element_id not in element_attempts:
            element_attempts[attempt.element_id] = []
        element_attempts[attempt.element_id].append(attempt)
    
    # Calculate and update difficulties
    for element_id, element_attempts_list in element_attempts.items():
        difficulty_score = calculate_card_difficulty(element_attempts_list)
        
        # Update or create difficulty record
        difficulty = db.query(CardDifficulty).filter(
            and_(
                CardDifficulty.user_id == user_id,
                CardDifficulty.element_id == element_id
            )
        ).first()
        
        if not difficulty:
            difficulty = CardDifficulty(
                user_id=user_id,
                element_id=element_id
            )
            db.add(difficulty)
        
        difficulty.difficulty_score = difficulty_score
        difficulty.error_rate = 1.0 - (sum(1 for a in element_attempts_list if a.is_correct) / len(element_attempts_list))
        difficulty.average_response_time = sum(a.response_time_ms for a in element_attempts_list if a.response_time_ms) / len(element_attempts_list) / 1000.0
        difficulty.last_calculated = datetime.utcnow()
    
    db.commit()
