"""API package"""
from app.api.routes import auth_router, documents_router, search_router
from app.api.deps import get_db, get_current_user

__all__ = [
    "auth_router",
    "documents_router",
    "search_router",
    "get_db",
    "get_current_user",
]
