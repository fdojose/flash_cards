"""
Session Models

Defines SQLAlchemy models for learning sessions and user progress tracking.
Based on the flashcard learning logic specification.
"""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Import shared Base from database configuration
from app.database import Base


class UserLearningSet(Base):
    """User's active learning set for a dataset"""
    __tablename__ = "user_learning_sets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    stage = Column(Integer, default=1)  # Progressive stage (1=10 items, 2=20 items, etc.)
    status = Column(String(50), default="active")  # "active", "paused", "archived", "completed"
    mode = Column(String(50), default="progressive")  # "progressive", "fixed"
    is_paused = Column(Boolean, default=False)
    
    # Chunked learning fields
    chunk_number = Column(Integer, default=1)  # Current chunk (1, 2, 3, ...)
    total_chunks = Column(Integer)  # Total number of chunks for this dataset
    chunk_size = Column(Integer)  # Size of current chunk (adaptive: 100→75→60→50)
    total_dataset_size = Column(Integer)  # Total elements in the dataset
    
    # Staged isolation learning fields
    current_batch_start = Column(Integer, default=1)      # Start position of current batch (e.g., 6)
    current_batch_end = Column(Integer, default=None)     # End position of current batch (e.g., 10)  
    isolation_phase = Column(Boolean, default=True)       # True = learning new batch in isolation
    mastered_up_to = Column(Integer, default=0)          # Highest position fully mastered
    batch_size = Column(Integer, default=5)              # Size of each learning batch
    
    # Spiral learning tracking fields
    completed_integration_cycles = Column(Integer, default=0)      # Count of completed integration cycles
    spiral_review_mode = Column(Boolean, default=False)           # Currently in spiral review session
    last_spiral_review = Column(DateTime(timezone=True))          # Timestamp of last spiral review
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("UserLearningSetItem", back_populates="learning_set", cascade="all, delete-orphan")


class UserLearningSetItem(Base):
    """Individual items in a user's learning set"""
    __tablename__ = "user_learning_set_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_set_id = Column(UUID(as_uuid=True), ForeignKey("user_learning_sets.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer)  # Optional ordering within the set
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    learning_set = relationship("UserLearningSet", back_populates="items")


class UserElementReview(Base):
    """Spaced repetition tracking for user-element pairs"""
    __tablename__ = "user_element_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False)
    
    # Spaced repetition data
    success_streak = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True))
    next_due = Column(DateTime(timezone=True))
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Integer, default=250)  # Stored as integer (2.5 * 100)
    
    # Status tracking
    status = Column(String(50), default="new")  # "new", "learning", "due", "mastered", "integration_review"
    is_difficult = Column(Boolean, default=False)
    
    # Percentage-based mastery tracking
    accuracy_percentage = Column(Float, default=0.0)      # Current accuracy percentage (0.0 to 1.0)
    attempts_in_window = Column(Integer, default=0)       # Number of attempts in current review window
    
    # FSRS Integration tracking fields
    integration_confirmed = Column(Boolean, default=False)  # Has card been confirmed in integration phase
    integration_attempts = Column(Integer, default=0)      # Count of integration phase attempts
    last_integration_attempt = Column(DateTime(timezone=True))  # Timestamp of last integration attempt
    stability_score = Column(Float, default=1.0)           # FSRS stability S (days to desired retention)
    difficulty = Column(Float, default=5.0)                # FSRS difficulty D (1=easy … 10=hard)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserFieldAttempt(Base):
    """Individual question-answer attempts for detailed tracking"""
    __tablename__ = "user_field_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False)
    
    question_field = Column(String(255), nullable=False)  # Which field was shown
    answer_field = Column(String(255), nullable=False)    # Which field was being asked
    user_answer = Column(Text)  # What the user selected/typed
    correct_answer = Column(Text, nullable=False)  # The correct answer
    is_correct = Column(Boolean, nullable=False)
    
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    response_time_ms = Column(Integer)  # Time taken to answer in milliseconds
