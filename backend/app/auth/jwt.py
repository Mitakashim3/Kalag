"""
Kalag JWT Token Utilities
Handles creation and validation of access and refresh tokens
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import hashlib
import secrets

from app.config import settings


class TokenError(Exception):
    """Custom exception for token-related errors"""
    pass


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a short-lived access token.
    
    Args:
        data: Payload data (typically {"sub": user_id})
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str, datetime]:
    """
    Create a long-lived refresh token.
    
    Returns:
        Tuple of (raw_token, token_hash, expires_at)
        - raw_token: Send to client in HttpOnly cookie
        - token_hash: Store in database for validation
        - expires_at: Token expiration datetime
    """
    # Generate a cryptographically secure random token
    raw_token = secrets.token_urlsafe(32)
    
    # Hash the token for storage (never store raw tokens)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    if expires_delta:
        expires_at = datetime.utcnow() + expires_delta
    else:
        expires_at = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    return raw_token, token_hash, expires_at


def hash_refresh_token(raw_token: str) -> str:
    """Hash a raw refresh token for database lookup"""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate an access token.
    
    Args:
        token: JWT string
        
    Returns:
        Decoded payload
        
    Raises:
        TokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Verify it's an access token
        if payload.get("type") != "access":
            raise TokenError("Invalid token type")
        
        # Verify subject exists
        if not payload.get("sub"):
            raise TokenError("Token missing subject")
            
        return payload
        
    except JWTError as e:
        raise TokenError(f"Invalid token: {str(e)}")


def get_token_expiry_seconds() -> int:
    """Get access token expiry in seconds (for frontend)"""
    return settings.access_token_expire_minutes * 60
