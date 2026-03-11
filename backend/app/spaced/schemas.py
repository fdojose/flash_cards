"""
Spaced Repetition Schemas

Pydantic models for spaced repetition request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class SpacedConfigResponse(BaseModel):
    """Response for spaced repetition configuration"""
    user_id: UUID
    algorithm: str
    initial_ease: float
    minimum_ease: float
    maximum_ease: float
    ease_bonus: float
    ease_penalty: float
    initial_interval: int
    graduation_interval: int
    maximum_interval: int
    learning_steps: str
    relearning_steps: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SpacedConfigUpdate(BaseModel):
    """Request to update spaced repetition configuration"""
    algorithm: Optional[str] = None
    initial_ease: Optional[float] = Field(None, ge=1.0, le=5.0)
    minimum_ease: Optional[float] = Field(None, ge=1.0, le=3.0)
    maximum_ease: Optional[float] = Field(None, ge=2.0, le=10.0)
    ease_bonus: Optional[float] = Field(None, ge=0.0, le=1.0)
    ease_penalty: Optional[float] = Field(None, ge=0.0, le=1.0)
    initial_interval: Optional[int] = Field(None, ge=1, le=30)
    graduation_interval: Optional[int] = Field(None, ge=1, le=30)
    maximum_interval: Optional[int] = Field(None, ge=30, le=3650)
    learning_steps: Optional[str] = None
    relearning_steps: Optional[str] = None


class ReviewSessionResponse(BaseModel):
    """Response for review session data"""
    id: UUID
    session_type: str
    cards_reviewed: int
    cards_correct: int
    total_time_ms: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CardDifficultyResponse(BaseModel):
    """Response for card difficulty analysis"""
    id: UUID
    element_id: UUID
    average_response_time: Optional[float] = None
    error_rate: float
    difficulty_score: float
    learning_velocity: float
    retention_rate: float
    first_seen: Optional[datetime] = None
    last_calculated: datetime
    
    class Config:
        from_attributes = True


class OptimalScheduleResponse(BaseModel):
    """Response for optimal review schedule"""
    target_retention: float
    daily_review_limit: int
    preferred_study_time: Optional[str] = None
    next_7_days_count: int
    next_30_days_count: int
    optimal_session_length: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SpacedAnalyticsResponse(BaseModel):
    """Response for spaced repetition analytics"""
    total_reviews: int
    total_attempts: int
    accuracy_percentage: float
    mastered_cards: int
    learning_cards: int
    due_cards: int
    average_ease_factor: float
    retention_rate: float
    days_analyzed: int


class IntervalCalculationRequest(BaseModel):
    """Request for interval calculation"""
    current_ease: float
    success_streak: int
    was_correct: bool
    response_time_ms: Optional[int] = None


class IntervalCalculationResponse(BaseModel):
    """Response for interval calculation"""
    new_interval: int
    new_ease: float
    next_due: datetime
    algorithm_used: str
