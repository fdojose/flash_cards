#!/usr/bin/env python3
"""
Quick script to create a test user for SQLite database
"""
import os
import sys
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, UUID, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from passlib.context import CryptContext
import uuid

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Database setup
DATABASE_URL = "sqlite:///./flashcard_test.db"
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

# Simple User model compatible with SQLite
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """Create a test user"""
    
    # Check if user already exists
    existing_user = session.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        print("✅ Test user already exists!")
        print(f"   Email: {existing_user.email}")
        print(f"   Name: {existing_user.name}")
        return
    
    # Create new user
    hashed_password = pwd_context.hash("password123")
    
    test_user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=hashed_password,
        is_active=True,
        is_admin=True
    )
    
    session.add(test_user)
    session.commit()
    
    print("✅ Test user created successfully!")
    print("   Email: test@example.com")
    print("   Password: password123")
    print("   Admin: Yes")

if __name__ == "__main__":
    try:
        create_test_user()
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
    finally:
        session.close()
