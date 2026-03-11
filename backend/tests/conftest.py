#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Test Configuration and Fixtures
========================================================

Comprehensive test setup for the flashcard learning system:
- Test database setup with SQLite in-memory
- Authentication fixtures for testing
- Mock data generators
- Test utilities and helpers
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.auth.models import User
from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
from app.sessions.models import Session, FlashCard, Response
from app.spaced.models import SpacedCard
from app.gamification.models import Achievement, UserAchievement
from app.auth.utils import get_password_hash, create_access_token

# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with proper configuration for SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db() -> Generator:
    """Create a fresh database for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override"""
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com", 
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpassword123", 
        "full_name": "Admin User",
        "is_admin": True
    }

@pytest.fixture
def test_user(test_db, test_user_data):
    """Create a test user in the database"""
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_admin(test_db, test_admin_data):
    """Create a test admin user in the database"""
    admin = User(
        username=test_admin_data["username"], 
        email=test_admin_data["email"],
        hashed_password=get_password_hash(test_admin_data["password"]),
        full_name=test_admin_data["full_name"],
        is_admin=True
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin

@pytest.fixture
def user_token(test_user):
    """Generate JWT token for test user"""
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture
def admin_token(test_admin):
    """Generate JWT token for test admin"""
    return create_access_token(data={"sub": test_admin.username})

@pytest.fixture
def auth_headers(user_token):
    """Authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Authorization headers for admin requests"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def sample_dataset_data():
    """Sample dataset data for testing"""
    return {
        "name": "Spanish Vocabulary",
        "description": "Basic Spanish words for beginners",
        "elements": [
            {
                "code": "SP-001",
                "fields": {
                    "spanish": "hola",
                    "english": "hello", 
                    "category": "greetings"
                }
            },
            {
                "code": "SP-002", 
                "fields": {
                    "spanish": "adiós",
                    "english": "goodbye",
                    "category": "greetings"
                }
            },
            {
                "code": "SP-003",
                "fields": {
                    "spanish": "casa",
                    "english": "house",
                    "category": "nouns"
                }
            }
        ]
    }

@pytest.fixture
def test_dataset(test_db, sample_dataset_data):
    """Create a test dataset with elements and fields"""
    from uuid import uuid4
    from datetime import datetime
    
    dataset = Dataset(
        id=uuid4(),
        name=sample_dataset_data["name"],
        description=sample_dataset_data["description"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(dataset)
    test_db.commit()
    test_db.refresh(dataset)
    
    # Create elements and fields
    for element_data in sample_dataset_data["elements"]:
        element = Element(
            id=uuid4(),
            dataset_id=dataset.id,
            code=element_data["code"],
            created_at=datetime.utcnow()
        )
        test_db.add(element)
        test_db.commit()
        test_db.refresh(element)
        
        for field_name, field_value in element_data["fields"].items():
            field = Field(
                id=uuid4(),
                element_id=element.id,
                field_name=field_name,
                field_value=field_value,
                field_type="text",
                media_url=None
            )
            test_db.add(field)
        
        test_db.commit()
    
    return dataset

@pytest.fixture
def test_session(test_db, test_user, test_dataset):
    """Create a test learning session"""
    from uuid import uuid4
    from datetime import datetime
    
    session = Session(
        id=uuid4(),
        user_id=test_user.id,
        dataset_id=test_dataset.id,
        session_type="practice",
        status="active",
        settings={
            "shuffle_cards": True,
            "reverse_mode": False,
            "auto_advance": False,
            "show_hints": True
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session

@pytest.fixture
def test_flashcards(test_db, test_session, test_dataset):
    """Create test flashcards for a session"""
    from uuid import uuid4
    from datetime import datetime
    
    # Get elements from the dataset
    elements = test_db.query(Element).filter(Element.dataset_id == test_dataset.id).all()
    flashcards = []
    
    for i, element in enumerate(elements):
        flashcard = FlashCard(
            id=uuid4(),
            session_id=test_session.id,
            element_id=element.id,
            front_field="spanish",
            back_field="english",
            order_index=i,
            status="pending",
            created_at=datetime.utcnow()
        )
        test_db.add(flashcard)
        flashcards.append(flashcard)
    
    test_db.commit()
    for flashcard in flashcards:
        test_db.refresh(flashcard)
    
    return flashcards

@pytest.fixture
def test_responses(test_db, test_flashcards, test_user):
    """Create test responses for flashcards"""
    from uuid import uuid4
    from datetime import datetime
    
    responses = []
    for i, flashcard in enumerate(test_flashcards):
        response = Response(
            id=uuid4(),
            session_id=flashcard.session_id,
            flashcard_id=flashcard.id,
            user_id=test_user.id,
            response_time=2.5 + i * 0.5,  # Varying response times
            confidence=4 if i % 2 == 0 else 3,  # Alternating confidence
            is_correct=i % 3 != 0,  # Mix of correct/incorrect
            created_at=datetime.utcnow()
        )
        test_db.add(response)
        responses.append(response)
    
    test_db.commit()
    for response in responses:
        test_db.refresh(response)
    
    return responses

@pytest.fixture
def test_achievements(test_db):
    """Create test achievements"""
    from uuid import uuid4
    from datetime import datetime
    
    achievements = [
        Achievement(
            id=uuid4(),
            name="First Steps",
            description="Complete your first session",
            badge_icon="🎯", 
            unlock_criteria={"sessions_completed": 1},
            points_reward=10,
            created_at=datetime.utcnow()
        ),
        Achievement(
            id=uuid4(),
            name="Streak Master",
            description="Maintain a 7-day learning streak",
            badge_icon="🔥",
            unlock_criteria={"daily_streak": 7},
            points_reward=50,
            created_at=datetime.utcnow()
        ),
        Achievement(
            id=uuid4(),
            name="Perfect Score",
            description="Get 100% accuracy in a session",
            badge_icon="⭐",
            unlock_criteria={"perfect_session": True},
            points_reward=25,
            created_at=datetime.utcnow()
        )
    ]
    
    for achievement in achievements:
        test_db.add(achievement)
    
    test_db.commit()
    for achievement in achievements:
        test_db.refresh(achievement)
    
    return achievements

# Async test utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test data generators
class TestDataGenerator:
    """Utility class for generating test data"""
    
    @staticmethod
    def create_user_data(username="testuser", email="test@example.com", is_admin=False):
        """Generate user data"""
        return {
            "username": username,
            "email": email,
            "password": "testpassword123",
            "full_name": f"Test User {username}",
            "is_admin": is_admin
        }
    
    @staticmethod
    def create_dataset_data(name="Test Dataset", num_elements=3):
        """Generate dataset data with specified number of elements"""
        elements = []
        for i in range(num_elements):
            elements.append({
                "code": f"TEST-{i+1:03d}",
                "fields": {
                    "question": f"Test question {i+1}",
                    "answer": f"Test answer {i+1}",
                    "category": "test"
                }
            })
        
        return {
            "name": name,
            "description": f"Test dataset with {num_elements} elements",
            "elements": elements
        }
    
    @staticmethod
    def create_session_settings(shuffle=True, reverse=False, auto_advance=False):
        """Generate session settings"""
        return {
            "shuffle_cards": shuffle,
            "reverse_mode": reverse, 
            "auto_advance": auto_advance,
            "show_hints": True,
            "time_limit": None
        }

# Export fixtures and utilities
__all__ = [
    "test_db",
    "client", 
    "test_user_data",
    "test_admin_data",
    "test_user",
    "test_admin",
    "user_token",
    "admin_token",
    "auth_headers",
    "admin_headers",
    "sample_dataset_data",
    "test_dataset",
    "test_session",
    "test_flashcards",
    "test_responses",
    "test_achievements",
    "TestDataGenerator"
]
