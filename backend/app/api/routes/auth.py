"""
Kalag Auth API Routes
Handles login, registration, token refresh, and logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import User, RefreshToken
from app.db.schemas import (
    UserCreate, UserLogin, UserResponse,
    TokenResponse, RefreshResponse
)
from app.auth import (
    hash_password, verify_password, validate_password_strength, sanitize_email,
    create_access_token, create_refresh_token, hash_refresh_token,
    get_token_expiry_seconds, validate_refresh_token_cookie, get_current_user
)
from app.security import limiter, AUTH_RATE_LIMIT
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - Validates email uniqueness
    - Enforces password strength requirements
    - Returns user profile (no auto-login)
    """
    # Sanitize email
    email = sanitize_email(user_data.email)
    
    # Check if user exists
    existing = await db.execute(
        select(User).where(User.email == email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create user
    user = User(
        email=email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and issue tokens.
    
    TOKEN STRATEGY:
    - access_token: Returned in response body, stored in memory (React state)
    - refresh_token: Set as HttpOnly cookie (XSS protection)
    
    This ensures:
    - XSS cannot steal the refresh token
    - CSRF is mitigated by requiring the access token in headers
    """
    email = sanitize_email(credentials.email)
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Create refresh token
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    
    # Store refresh token in database
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )
    db.add(refresh_token_record)
    await db.commit()
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,  # JavaScript cannot access
        secure=settings.cookie_secure,  # HTTPS only in production
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"  # Only sent to auth endpoints
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds()
    )


@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh_token(
    request: Request,
    response: Response,
    token_data: tuple = Depends(validate_refresh_token_cookie),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using the HttpOnly cookie.
    
    SILENT REFRESH FLOW:
    1. Frontend calls this endpoint when access token is about to expire
    2. Browser automatically sends the HttpOnly cookie
    3. We validate the cookie, issue new tokens
    4. Old refresh token is rotated (revoked, new one issued)
    
    This allows users to stay logged in without re-entering credentials.
    """
    user, old_token = token_data
    
    # Revoke old refresh token (rotation)
    old_token.revoked = True
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Create new refresh token (rotation)
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    
    new_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )
    db.add(new_refresh_token)
    await db.commit()
    
    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"
    )
    
    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_token_expiry_seconds()
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking all refresh tokens.
    
    This ensures logout works across all devices.
    """
    # Revoke all refresh tokens for this user
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .where(RefreshToken.revoked == False)
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.revoked = True
    
    await db.commit()
    
    # Clear the cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth"
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user
