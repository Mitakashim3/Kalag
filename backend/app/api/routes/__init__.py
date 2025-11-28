"""API Routes package"""
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.search import router as search_router

__all__ = [
    "auth_router",
    "documents_router", 
    "search_router",
]
