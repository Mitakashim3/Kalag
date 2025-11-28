"""Auth package"""
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_refresh_token,
    get_token_expiry_seconds,
    TokenError
)
from app.auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    sanitize_email
)
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    validate_refresh_token_cookie,
    get_optional_user
)

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token", 
    "decode_access_token",
    "hash_refresh_token",
    "get_token_expiry_seconds",
    "TokenError",
    # Security
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "sanitize_email",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "validate_refresh_token_cookie",
    "get_optional_user",
]
