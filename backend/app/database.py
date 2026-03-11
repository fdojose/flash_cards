"""
Database Configuration

SQLAlchemy database setup and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flashcard_user:dev_password@localhost:5433/flashcard_dev"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    
    This function provides a database session for FastAPI dependency injection.
    It ensures the session is properly closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models to register them with SQLAlchemy
    from .auth.models import User, UserRole, PasswordResetToken
    from .datasets.models import Dataset, Element, Field, Tag, ElementTag
    from .sessions.models import UserLearningSet, UserLearningSetItem, UserElementReview, UserFieldAttempt
    from .gamification.models import UserAchievement, UserStreak, LeaderboardScore, BadgeDefinition
    from .spaced.models import SpacedRepetitionConfig, ReviewSession, CardDifficulty, OptimalSchedule
    from .dashboard.models import UserStats, DatasetProgress, StudySession, WeeklyGoal, LearningInsight
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
