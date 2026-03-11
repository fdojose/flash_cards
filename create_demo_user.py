#!/usr/bin/env python3
"""
Create a demo user for testing the flashcard application
"""

import sys
import os
from datetime import datetime
from passlib.context import CryptContext
import psycopg2
import uuid

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database configuration
DB_CONFIG = {
    "host": "postgres",  # Use service name in Docker network
    "port": 5432,
    "database": "flashcard_dev",
    "user": "flashcard_user",
    "password": "dev_password"
}

def create_demo_user():
    """Create a demo user in the database"""
    
    demo_users = [
        {
            "name": "Demo User",
            "email": "demo@example.com",
            "password": "demo123",
            "is_admin": False
        },
        {
            "name": "Admin User",
            "email": "admin@example.com", 
            "password": "admin123",
            "is_admin": True
        }
    ]
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        for user_data in demo_users:
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (user_data["email"],)
            )
            existing = cursor.fetchone()
            
            if existing:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
                continue
            
            # Hash password
            hashed_password = pwd_context.hash(user_data["password"])
            
            # Create user
            user_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            cursor.execute("""
                INSERT INTO users (id, name, email, hashed_password, is_admin, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, user_data["name"], user_data["email"], hashed_password, 
                  user_data["is_admin"], True, now, now))
            
            role = "Admin" if user_data["is_admin"] else "User"
            print(f"✅ Created {role}: {user_data['name']} ({user_data['email']})")
            print(f"   Password: {user_data['password']}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("\n🎉 Demo users created successfully!")
        print("\n📋 Test Credentials:")
        print("   Regular User: demo@example.com / demo123")
        print("   Admin User:   admin@example.com / admin123")
        
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_demo_user()
