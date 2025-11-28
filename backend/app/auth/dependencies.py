"""
Kalag Auth Dependencies
FastAPI dependencies for authentication and authorization

This module contains the critical auth middleware that:
1. Extracts access token from Authorization header
2. Validates refresh token from HttpOnly cookie
3. Provides current user to route handlers
"""

from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.database import get_db
from app.db.models import User, RefreshToken
from app.auth.jwt import decode_access_token, hash_refresh_token, TokenError


# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from access token.
    
    This is the primary auth dependency used by protected routes.
    It extracts the JWT from the Authorization header and validates it.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException 401: If token is missing, invalid, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check for Bearer token in header
    if not credentials:
        raise credentials_exception
    
    try:
        # Decode and validate the access token
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except TokenError:
        raise credentials_exception
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures user is active.
    Use this for routes that require an active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency for admin-only routes.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def validate_refresh_token_cookie(
    request: Request,
    refresh_token: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db)
) -> tuple[User, RefreshToken]:
    """
    Validate refresh token from HttpOnly cookie.
    
    This is the KEY SECURITY FUNCTION for token refresh.
    The refresh token is:
    1. Stored in an HttpOnly cookie (not accessible via JavaScript - XSS protection)
    2. Hashed before database lookup (tokens never stored in plain text)
    3. Checked for expiration and revocation
    
    Args:
        request: FastAPI request for cookie access
        refresh_token: The refresh token from the HttpOnly cookie
        db: Database session
        
    Returns:
        Tuple of (User, RefreshToken) if valid
        
    Raises:
        HTTPException 401: If token is missing, invalid, expired, or revoked
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hash the token to look up in database
    token_hash = hash_refresh_token(refresh_token)
    
    # Find the token in database
    from datetime import datetime
    
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.revoked == False)
        .where(RefreshToken.expires_at > datetime.utcnow())
    )
    stored_token = result.scalar_one_or_none()
    
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user
    result = await db.execute(
        select(User).where(User.id == stored_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user, stored_token


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional auth dependency - returns None if not authenticated.
    Use for routes that work differently for logged-in users.
    """
    if not credentials:
        return None
    
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if not user_id:
            return None
            
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
        
    except TokenError:
        return None
