"""
Dashboard Models

Defines SQLAlchemy models for dashboard analytics and cached statistics.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base


class UserStats(Base):
    """Cached user statistics for dashboard performance"""
    __tablename__ = "user_stats"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Learning statistics
    total_elements_seen = Column(Integer, default=0)
    total_elements_mastered = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    total_study_time_minutes = Column(Integer, default=0)
    
    # Performance metrics
    overall_accuracy = Column(Float, default=0.0)  # Percentage 0-100
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    
    # Progress tracking
    active_datasets = Column(Integer, default=0)
    completed_datasets = Column(Integer, default=0)
    
    # Time-based metrics
    avg_session_length_minutes = Column(Float, default=0.0)
    sessions_this_week = Column(Integer, default=0)
    sessions_this_month = Column(Integer, default=0)
    
    # Calculated metrics
    mastery_rate = Column(Float, default=0.0)  # Percentage of seen elements mastered
    learning_velocity = Column(Float, default=1.0)  # How fast user learns (multiplier)
    retention_rate = Column(Float, default=0.9)  # How well user retains knowledge
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DatasetProgress(Base):
    """Progress tracking per dataset per user"""
    __tablename__ = "dataset_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    
    # Progress metrics
    elements_in_dataset = Column(Integer, default=0)
    elements_seen = Column(Integer, default=0)
    elements_mastered = Column(Integer, default=0)
    current_stage = Column(Integer, default=1)
    
    # Performance metrics
    accuracy_rate = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)  # Seconds
    total_study_time = Column(Integer, default=0)  # Minutes
    
    # Status tracking
    status = Column(String(50), default="active")  # "active", "completed", "paused"
    completion_percentage = Column(Float, default=0.0)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_studied = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Ensure one progress record per user-dataset pair
    __table_args__ = (
        UniqueConstraint('user_id', 'dataset_id', name='uq_dataset_progress_user_dataset'),
    )


class StudySession(Base):
    """Detailed study session tracking for analytics"""
    __tablename__ = "study_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True)
    
    # Session data
    session_type = Column(String(50), default="review")  # "review", "learning", "practice"
    cards_studied = Column(Integer, default=0)
    cards_correct = Column(Integer, default=0)
    cards_new = Column(Integer, default=0)  # New cards introduced
    cards_due = Column(Integer, default=0)  # Due cards reviewed
    
    # Timing data
    duration_minutes = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)  # Seconds per card
    
    # Performance metrics
    accuracy_rate = Column(Float, default=0.0)
    improvement_score = Column(Float, default=0.0)  # Compared to previous sessions
    
    # Session metadata
    device_type = Column(String(50))  # "mobile", "desktop", "tablet"
    time_of_day = Column(String(20))  # "morning", "afternoon", "evening", "night"
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))


class WeeklyGoal(Base):
    """User's weekly learning goals and progress"""
    __tablename__ = "weekly_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Goal settings
    target_sessions_per_week = Column(Integer, default=5)
    target_minutes_per_week = Column(Integer, default=150)  # 30 min * 5 days
    target_cards_per_week = Column(Integer, default=100)
    
    # Progress tracking
    week_start_date = Column(DateTime(timezone=True), nullable=False)
    sessions_completed = Column(Integer, default=0)
    minutes_studied = Column(Integer, default=0)
    cards_studied = Column(Integer, default=0)
    
    # Achievement tracking
    goal_achieved = Column(Boolean, default=False)
    streak_weeks = Column(Integer, default=0)  # Consecutive weeks achieving goals
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LearningInsight(Base):
    """AI-generated insights about user's learning patterns"""
    __tablename__ = "learning_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Insight data
    insight_type = Column(String(100), nullable=False)  # "performance", "pattern", "recommendation"
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")  # "low", "medium", "high"
    
    # Data used for insight
    data_points = Column(JSON)  # Metadata about the analysis
    confidence_score = Column(Float, default=0.0)  # 0-1 confidence in the insight
    
    # Status
    is_read = Column(Boolean, default=False)
    is_actionable = Column(Boolean, default=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # When insight becomes stale


class UserGameStats(Base):
    """Extended gamification statistics for ranking system"""
    __tablename__ = "user_game_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Core performance metrics
    total_cards_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_response_time_ms = Column(Integer, default=0)
    
    # Derived metrics
    accuracy_percentage = Column(Float, default=0.0)  # calculated: (correct_answers / total_cards_answered) * 100
    average_response_time_ms = Column(Integer, default=0)  # calculated: total_response_time_ms / total_cards_answered
    
    # Gamification metrics
    cards_mastered = Column(Integer, default=0)
    study_streak_days = Column(Integer, default=0)
    total_study_sessions = Column(Integer, default=0)
    
    # Ranking scores
    speed_score = Column(Float, default=0.0)  # Volume-weighted speed score
    overall_score = Column(Float, default=0.0)  # Combined ranking score
    
    # Experience and levels
    experience_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    achievements_count = Column(Integer, default=0)
    
    # Timestamps
    last_activity_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# UserAchievement model has been moved to gamification.models to avoid conflicts
# Import from ..gamification.models import UserAchievement when needed


class DailyStats(Base):
    """Daily statistics for streak tracking"""
    __tablename__ = "daily_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    date = Column(DateTime(timezone=True), nullable=False)  # date of activity
    cards_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    study_time_minutes = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Unique constraint to ensure one record per user per day
    __table_args__ = (UniqueConstraint('user_id', 'date', name='user_daily_stats_unique'),)
