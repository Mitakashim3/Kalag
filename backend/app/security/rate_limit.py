"""
Kalag Rate Limiting Configuration
Using slowapi to prevent DDoS and brute force attacks on free tier
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses user ID if authenticated, otherwise IP address.
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Initialize limiter
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri="memory://",  # Use Redis in production for distributed rate limiting
)


# ===========================================
# Rate Limit Decorators for Routes
# ===========================================

# Auth endpoints - relaxed for development (increase in production)
AUTH_RATE_LIMIT = "60/minute"

# Search endpoints - moderate limits
SEARCH_RATE_LIMIT = "60/minute"

# Upload endpoints - strict limits due to resource usage
UPLOAD_RATE_LIMIT = "20/minute"

# General API endpoints
DEFAULT_RATE_LIMIT = f"{settings.rate_limit_per_minute}/minute"


def setup_rate_limiting(app):
    """
    Configure rate limiting for the FastAPI app.
    Call this in main.py during app initialization.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
