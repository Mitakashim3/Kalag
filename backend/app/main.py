"""
Kalag - Internal RAG Tool for Businesses
FastAPI Main Application Entry Point

This is the main application file that:
1. Initializes the FastAPI app with CORS and security middleware
2. Sets up rate limiting
3. Registers all API routes
4. Handles startup/shutdown events for database and vector store
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.db import init_db, close_db
from app.rag import get_vector_store
from app.security import SecurityHeadersMiddleware, setup_rate_limiting, PromptInjectionError
from app.api import auth_router, documents_router, search_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Kalag API...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize vector store
    vector_store = get_vector_store()
    await vector_store.initialize()
    logger.info("Vector store initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kalag API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Kalag API",
    description="Internal RAG Tool for Businesses - Multi-modal document search with visual citations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ===========================================
# Middleware Setup
# ===========================================

# CORS - Configure for your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers for cross-origin with credentials
    expose_headers=["X-Request-ID"],
)

# Security Headers (Helmet equivalent)
app.add_middleware(SecurityHeadersMiddleware)

# Rate Limiting
setup_rate_limiting(app)


# ===========================================
# Exception Handlers
# ===========================================

@app.exception_handler(PromptInjectionError)
async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
    """Handle prompt injection attempts."""
    logger.warning(f"Prompt injection attempt from {request.client.host}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid query detected. Please rephrase your question."}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


# ===========================================
# API Routes
# ===========================================

# Mount all routes under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(search_router, prefix="/api")


# ===========================================
# Health Check
# ===========================================

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Used by Render/Vercel for health checks.
    """
    return {
        "status": "healthy",
        "service": "kalag-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "Kalag API",
        "docs": "/api/docs",
        "health": "/api/health"
    }


# ===========================================
# Development Server
# ===========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
