"""
Spaced Repetition Models

Extensions to the core review models for advanced spaced repetition features.
These models complement the UserElementReview model in the sessions module.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base


class SpacedRepetitionConfig(Base):
    """Configuration for spaced repetition algorithms per user"""
    __tablename__ = "spaced_repetition_configs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    algorithm = Column(String(50), default="sm2")  # "sm2", "fsrs", "anki"
    
    # SM-2 Algorithm parameters (kept for backward compatibility)
    initial_ease = Column(Float, default=2.5)
    minimum_ease = Column(Float, default=1.3)
    maximum_ease = Column(Float, default=5.0)
    ease_bonus = Column(Float, default=0.15)
    ease_penalty = Column(Float, default=0.2)

    # Interval parameters
    initial_interval = Column(Integer, default=1)    # Days
    graduation_interval = Column(Integer, default=6) # Days to graduate from learning
    maximum_interval = Column(Integer, default=365)  # Maximum days between reviews

    # FSRS parameters
    desired_retention = Column(Float, default=0.9)   # Target retention rate (0.8–0.95)
    
    # Learning parameters
    learning_steps = Column(String(100), default="1,10,1440")  # Minutes: 1min, 10min, 1day
    relearning_steps = Column(String(100), default="10,1440")  # Minutes for failed cards
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReviewSession(Base):
    """Detailed review session tracking"""
    __tablename__ = "review_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True)
    
    session_type = Column(String(50), default="review")  # "review", "learning", "cramming"
    cards_reviewed = Column(Integer, default=0)
    cards_correct = Column(Integer, default=0)
    total_time_ms = Column(Integer, default=0)  # Session duration in milliseconds
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))


class CardDifficulty(Base):
    """Track card difficulty and learning patterns"""
    __tablename__ = "card_difficulties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False)
    
    # Difficulty metrics
    average_response_time = Column(Float)  # Average response time in seconds
    error_rate = Column(Float, default=0.0)  # Percentage of incorrect answers (0.0-1.0)
    difficulty_score = Column(Float, default=0.5)  # Computed difficulty (0.0-1.0)
    
    # Learning pattern analysis
    learning_velocity = Column(Float, default=1.0)  # How fast the user learns this card
    retention_rate = Column(Float, default=0.9)  # How well the user retains this card
    
    # Timestamps
    first_seen = Column(DateTime(timezone=True))
    last_calculated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure one record per user-element pair
    __table_args__ = (
        UniqueConstraint('user_id', 'element_id', name='uq_card_difficulty_user_element'),
    )


class OptimalSchedule(Base):
    """Pre-computed optimal review schedules"""
    __tablename__ = "optimal_schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Schedule parameters
    target_retention = Column(Float, default=0.9)  # Target retention rate (0.0-1.0)
    daily_review_limit = Column(Integer, default=50)  # Max cards per day
    preferred_study_time = Column(String(50))  # "morning", "afternoon", "evening"
    
    # Computed schedule data
    next_7_days_count = Column(Integer, default=0)  # Cards due in next 7 days
    next_30_days_count = Column(Integer, default=0)  # Cards due in next 30 days
    optimal_session_length = Column(Integer, default=20)  # Minutes
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
