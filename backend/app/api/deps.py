"""
Kalag API Dependencies
Shared dependencies for route handlers
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    get_optional_user
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user", 
    "get_current_superuser",
    "get_optional_user",
]
