"""
Gamification Models

Defines SQLAlchemy models for badges, streaks, and leaderboards.
"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base


class UserAchievement(Base):
    """User achievements and badges"""
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_title', name='_user_achievement_uc'),
        {'extend_existing': True}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_title = Column(String(255), nullable=False)
    achievement_description = Column(Text)
    badge_emoji = Column(String(10))  # Emoji or icon identifier
    date_awarded = Column(DateTime(timezone=True), server_default=func.now())


class UserStreak(Base):
    """User activity streaks"""
    __tablename__ = "user_streaks"
    __table_args__ = {'extend_existing': True}
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True))
    streak_type = Column(String(50), default="daily")  # "daily", "weekly", etc.
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LeaderboardScore(Base):
    """Leaderboard scores for different metrics"""
    __tablename__ = "leaderboard_scores"
    __table_args__ = (
        UniqueConstraint('user_id', 'score_type', 'dataset_id', 'period', name='_user_score_uc'),
        {'extend_existing': True}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    score_type = Column(String(100), nullable=False)  # "mastered", "streak", "sessions", "accuracy"
    value = Column(Integer, nullable=False)
    period = Column(String(50), default="all_time")  # "daily", "weekly", "monthly", "all_time"
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BadgeDefinition(Base):
    """Available badge definitions"""
    __tablename__ = "badge_definitions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(10))  # Emoji
    criteria_type = Column(String(100), nullable=False)  # "elements_mastered", "streak_days", etc.
    criteria_value = Column(Integer, nullable=False)  # Threshold value
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
