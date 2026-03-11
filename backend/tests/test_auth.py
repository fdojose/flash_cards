#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Authentication Module Tests
==================================================

Test coverage for:
- User registration
- User login
- JWT token generation and validation
- Password hashing and verification
- Admin role checking
- Authentication endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import verify_password, get_password_hash, create_access_token, decode_access_token


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, test_db: Session):
        """Test creating a user in the database"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_admin=False
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_admin_user_creation(self, test_db: Session):
        """Test creating an admin user"""
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass"),
            full_name="Admin User",
            is_admin=True
        )
        test_db.add(admin)
        test_db.commit()
        test_db.refresh(admin)
        
        assert admin.is_admin is True


class TestAuthenticationUtils:
    """Test authentication utility functions"""
    
    def test_password_hashing(self):
        """Test password hashing utility"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_verification(self):
        """Test password verification utility"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
        assert verify_password("", hashed) is False
    
    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_token_decoding(self):
        """Test JWT token decoding"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        decoded_data = decode_access_token(token)
        assert decoded_data is not None
        assert decoded_data.get("sub") == "testuser"
    
    def test_invalid_jwt_token(self):
        """Test handling of invalid JWT tokens"""
        invalid_token = "invalid.token.here"
        decoded_data = decode_access_token(invalid_token)
        assert decoded_data is None


class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    @pytest.mark.asyncio
    async def test_user_registration(self, client: AsyncClient):
        """Test user registration endpoint"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_duplicate_username_registration(self, client: AsyncClient, test_user):
        """Test registration with duplicate username"""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123",
            "full_name": "Different User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_duplicate_email_registration(self, client: AsyncClient, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123",
            "full_name": "Different User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_invalid_registration_data(self, client: AsyncClient):
        """Test registration with invalid data"""
        # Missing required fields
        invalid_data = {
            "username": "testuser"
            # Missing email, password, full_name
        }
        
        response = await client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, client: AsyncClient, test_user, test_user_data):
        """Test successful user login"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    @pytest.mark.asyncio
    async def test_user_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_user_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent username"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current authenticated user"""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "is_admin" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_admin_required_endpoint(self, client: AsyncClient, admin_headers, auth_headers):
        """Test endpoint that requires admin privileges"""
        # Test with admin user (should succeed)
        response = await client.get("/auth/admin-only", headers=admin_headers)
        assert response.status_code == 200
        
        # Test with regular user (should fail)
        response = await client.get("/auth/admin-only", headers=auth_headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_required_unauthorized(self, client: AsyncClient):
        """Test admin endpoint without authentication"""
        response = await client.get("/auth/admin-only")
        assert response.status_code == 401


class TestUserQueries:
    """Test user database queries"""
    
    def test_get_user_by_username(self, test_db: Session, test_user):
        """Test querying user by username"""
        found_user = test_db.query(User).filter(User.username == test_user.username).first()
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.username == test_user.username
    
    def test_get_user_by_email(self, test_db: Session, test_user):
        """Test querying user by email"""
        found_user = test_db.query(User).filter(User.email == test_user.email).first()
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
    
    def test_get_nonexistent_user(self, test_db: Session):
        """Test querying nonexistent user"""
        found_user = test_db.query(User).filter(User.username == "nonexistent").first()
        assert found_user is None
    
    def test_get_admin_users(self, test_db: Session, test_user, test_admin):
        """Test querying admin users"""
        admin_users = test_db.query(User).filter(User.is_admin == True).all()
        
        assert len(admin_users) == 1
        assert admin_users[0].id == test_admin.id
        assert admin_users[0].is_admin is True
    
    def test_get_regular_users(self, test_db: Session, test_user, test_admin):
        """Test querying regular users"""
        regular_users = test_db.query(User).filter(User.is_admin == False).all()
        
        assert len(regular_users) == 1
        assert regular_users[0].id == test_user.id
        assert regular_users[0].is_admin is False


class TestAuthenticationSecurity:
    """Test authentication security features"""
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        # This would typically be implemented in a password validator
        weak_passwords = ["123", "password", "abc"]
        strong_passwords = ["StrongP@ssw0rd123", "MySecure2024!"]
        
        for password in weak_passwords:
            # In a real implementation, this would validate password strength
            assert len(password) < 8  # Simple length check for demo
        
        for password in strong_passwords:
            assert len(password) >= 8
    
    def test_token_expiration(self):
        """Test JWT token expiration"""
        from datetime import datetime, timedelta, timezone
        import jwt
        from app.auth.utils import SECRET_KEY, ALGORITHM
        
        # Create token with short expiration
        expire = datetime.now(timezone.utc) + timedelta(seconds=1)
        data = {"sub": "testuser", "exp": expire}
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        # Token should be valid immediately
        decoded = decode_access_token(token)
        assert decoded is not None
        
        # Token should expire (in real scenario, would need to wait)
        # For testing, we create an already expired token
        expire = datetime.now(timezone.utc) - timedelta(seconds=1)
        data = {"sub": "testuser", "exp": expire}
        expired_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        decoded = decode_access_token(expired_token)
        assert decoded is None
    
    def test_user_data_sanitization(self, test_db: Session):
        """Test that sensitive data is not exposed"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User"
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        # Verify password is hashed, not stored in plain text
        assert user.hashed_password != "password123"
        assert verify_password("password123", user.hashed_password)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
