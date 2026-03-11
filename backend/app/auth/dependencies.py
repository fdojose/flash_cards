"""
Authentication Dependencies

Reusable FastAPI dependencies for JWT authentication and authorization.
These dependencies can be imported and used in other modules.
"""

import os
from datetime import datetime
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .models import User, UserRole
from ..database import get_db

# Security scheme
security = HTTPBearer()

# JWT settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    This dependency validates the JWT token and returns the authenticated user.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        # Check token expiration (redundant but explicit)
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure current user has admin privileges
    
    This dependency builds on get_current_user and additionally checks for admin role.
    Raises HTTPException if user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure current user is active (additional check beyond get_current_user)
    
    This is a more explicit dependency for routes that need to double-check user status.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    return current_user


def get_user_with_role(required_role: str):
    """
    Factory function to create role-specific dependencies
    
    Usage: get_user_with_role("admin"), get_user_with_role("moderator")
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user role from database
        user_role = db.query(UserRole).filter(UserRole.user_id == current_user.id).first()
        
        if not user_role or user_role.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return role_dependency


# Pre-configured role dependencies
get_moderator_user = get_user_with_role("moderator")
get_admin_role_user = get_user_with_role("admin")


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)] = None,
    db: Session = Depends(get_db)
) -> User | None:
    """
    Optional authentication dependency
    
    Returns the authenticated user if valid token is provided, None otherwise.
    Useful for routes that have different behavior for authenticated vs anonymous users.
    """
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            return None
            
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
            
        return user
    except JWTError:
        return None


def verify_token_only(token: str) -> dict | None:
    """
    Utility function to verify a token without database lookup
    
    Returns the token payload if valid, None otherwise.
    Useful for token validation in middleware or background tasks.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            return None
            
        return payload
    except JWTError:
        return None


async def require_same_user_or_admin(
    target_user_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user can only access their own data or is admin
    
    Usage in routes: 
    @router.get("/users/{user_id}/profile")
    async def get_user_profile(user_id: str, user: User = Depends(require_same_user_or_admin))
    """
    if str(current_user.id) != target_user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data"
        )
    return current_user


# Convenience imports for other modules
__all__ = [
    "get_current_user",
    "get_admin_user", 
    "get_active_user",
    "get_user_with_role",
    "get_moderator_user",
    "get_admin_role_user",
    "get_current_user_optional",
    "verify_token_only",
    "require_same_user_or_admin",
]
