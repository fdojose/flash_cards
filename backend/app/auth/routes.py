"""
Authentication Routes

FastAPI routes for user registration, login, and authentication.
"""
import os
import base64
import secrets
from datetime import datetime, timedelta
from typing import Annotated
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import requests as http_requests

from .models import User, UserRole, PasswordResetToken
from .schemas import UserCreate, UserLogin, UserResponse, Token, PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire.timestamp()})  # Convert to timestamp
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_reset_token() -> str:
    """Generate a secure random token for password reset"""
    return secrets.token_urlsafe(32)


def _gmail_get_access_token() -> str:
    """Exchange the stored refresh token for a short-lived access token."""
    resp = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_reset_email(email: str, token: str, user_name: str):
    """Send password reset email via Gmail API (OAuth2).

    Required environment variables:
        GOOGLE_CLIENT_ID      – OAuth2 client ID
        GOOGLE_CLIENT_SECRET  – OAuth2 client secret
        GOOGLE_REFRESH_TOKEN  – offline refresh token (run scripts/gmail_oauth_setup.py once)
        GMAIL_SENDER          – Gmail address to send from (must match the authorised account)
        APP_URL               – base URL for the reset link (default: http://localhost:3000)

    Falls back to console logging when any of the Google vars are missing.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN", "")
    gmail_sender = os.getenv("GMAIL_SENDER", "")
    app_url = os.getenv("APP_URL", "http://localhost:3000")

    reset_link = f"{app_url}/reset-password?token={token}"

    # Build MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your Flashcard App Password"
    msg["From"] = gmail_sender
    msg["To"] = email

    text_body = (
        f"Hello {user_name},\n\n"
        f"You requested a password reset for your Flashcard Learning System account.\n"
        f"Click the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        f"This link will expire in 1 hour.\n\n"
        f"If you didn't request this, please ignore this email.\n\n"
        f"Best regards,\nFlashcard Learning System"
    )
    html_body = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto">
      <h2>Reset Your Password</h2>
      <p>Hello <strong>{user_name}</strong>,</p>
      <p>You requested a password reset for your Flashcard Learning System account.</p>
      <p>
        <a href="{reset_link}" style="display:inline-block;padding:12px 24px;
           background:#2563eb;color:#fff;text-decoration:none;border-radius:6px">
          Reset Password
        </a>
      </p>
      <p>Or copy this link: <code>{reset_link}</code></p>
      <p>This link will expire in <strong>1 hour</strong>.</p>
      <p>If you didn't request this, you can safely ignore this email.</p>
      <hr/><p style="color:#6b7280;font-size:12px">Flashcard Learning System</p>
    </body></html>
    """
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    if not all([client_id, client_secret, refresh_token, gmail_sender]):
        # Gmail API not configured — log link for dev use
        print(
            f"\n[RESET EMAIL — Gmail API not configured]\n"
            f"To: {email}\n"
            f"Reset link: {reset_link}\n"
        )
        return True

    try:
        access_token = _gmail_get_access_token()
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        resp = http_requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        raise RuntimeError(f"Gmail API send failed: {exc}") from exc


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


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and return an access token (auto-login)"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create default user role
    user_role = UserRole(user_id=db_user.id, role="user")
    db.add(user_role)
    db.commit()

    # Issue token so the user is immediately logged in
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Example protected route"""
    return {"message": f"Hello {current_user.name}, this is a protected route!"}


@router.get("/admin-only")
async def admin_only_route(current_user: User = Depends(get_admin_user)):
    """Example admin-only route using is_admin flag"""
    return {"message": f"Hello admin {current_user.name}!", "admin_access": True}


@router.get("/admin-role-only")
async def admin_role_only_route(current_user: User = Depends(get_admin_role_user)):
    """Example admin-only route using role-based access"""
    return {"message": f"Hello admin {current_user.name}!", "role_access": True}


@router.get("/moderator-only")
async def moderator_only_route(current_user: User = Depends(get_moderator_user)):
    """Example moderator-only route"""
    return {"message": f"Hello moderator {current_user.name}!", "moderator_access": True}


@router.get("/public-or-user")
async def public_or_user_route(current_user: User = Depends(get_current_user_optional)):
    """Example route with optional authentication"""
    if current_user:
        return {
            "message": f"Hello authenticated user {current_user.name}!",
            "authenticated": True,
            "user_id": str(current_user.id)
        }
    else:
        return {
            "message": "Hello anonymous user!",
            "authenticated": False,
            "suggestion": "Login to get personalized content"
        }


@router.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Example route demonstrating same-user-or-admin access pattern"""
    # Check if user can access this profile
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own profile"
        )
    
    # Get target user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "profile": UserResponse.model_validate(target_user),
        "accessed_by": str(current_user.id),
        "is_admin_access": current_user.is_admin
    }


@router.get("/token/verify")
async def verify_token_route(current_user: User = Depends(get_current_user)):
    """Verify token validity and return user info"""
    return {
        "valid": True,
        "user": UserResponse.model_validate(current_user),
        "message": "Token is valid"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Session = Depends(get_db)
):
    """Issue a fresh token from a valid or recently-expired one.

    Accepts tokens that expired within the last 60 minutes so mid-session
    expiry is silently recovered on the client side.
    """
    GRACE_PERIOD_SECONDS = 3600  # 60 minutes

    try:
        # Decode without verifying expiry so we can apply our own grace window
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    exp = payload.get("exp")

    if not email or exp is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Allow refresh only within the grace period after expiry
    now = datetime.utcnow().timestamp()
    if now > exp + GRACE_PERIOD_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_token, "token_type": "bearer"}


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset for user"""
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration attacks
    # But only send email if user exists
    if user and user.is_active:
        # Clean up any existing tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        ).delete()
        
        # Generate new reset token
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        # Save token to database
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        
        # Send reset email (mock implementation for now)
        try:
            send_reset_email(user.email, token, user.name)
        except Exception as e:
            print(f"Failed to send reset email: {e}")
            # Don't fail the request if email sending fails
    
    return PasswordResetResponse(
        message="If an account with that email exists, a password reset link has been sent.",
        success=True
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    # Find valid reset token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Validate password (basic validation)
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    
    # Mark token as used
    reset_token.used_at = datetime.utcnow()
    
    db.commit()
    
    return PasswordResetResponse(
        message="Password has been reset successfully. You can now log in with your new password.",
        success=True
    )


@router.post("/verify-reset-token")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify if a reset token is valid"""
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"valid": True, "message": "Token is valid"}
