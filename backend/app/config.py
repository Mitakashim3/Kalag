"""
Kalag Backend Configuration
Centralized configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from pathlib import Path
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ===========================================
    # Application
    # ===========================================
    app_name: str = "Kalag"
    debug: bool = Field(default=False, env="DEBUG")
    
    # ===========================================
    # Security & Auth
    # ===========================================
    secret_key: str = Field(default="dev-secret-key-change-in-production-12345", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000", env="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _normalize_cors_origins(cls, value):
        # Support either comma-separated string or JSON-ish list env values.
        # Examples:
        # - https://a.com,https://b.com
        # - ["https://a.com","https://b.com"]
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(v) for v in value)
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    import json

                    parsed = json.loads(trimmed)
                    if isinstance(parsed, list):
                        return ",".join(str(v) for v in parsed)
                except Exception:
                    # Fall back to raw string.
                    return value
        return value
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    # Cookie Settings
    # For production cross-domain (Vercel + Render): domain=None, secure=True, samesite='none'
    # For local dev: domain=None, secure=False, samesite='lax'
    cookie_domain: Optional[str] = Field(default=None, env="COOKIE_DOMAIN")
    cookie_secure: bool = Field(default=False, env="COOKIE_SECURE")  # Set to True in production
    cookie_samesite: str = Field(default="lax", env="COOKIE_SAMESITE")  # Use 'none' for production cross-domain

    @field_validator("cookie_samesite", mode="before")
    @classmethod
    def _normalize_cookie_samesite(cls, value):
        # Render/Vercel dashboards often use capitalized values (e.g. "None").
        if value is None:
            return "lax"
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized == "none":
                return "none"
            if normalized in {"lax", "strict"}:
                return normalized
        return value
    
    # ===========================================
    # Database (SQLite default for development)
    # ===========================================
    database_url: str = Field(default="sqlite+aiosqlite:///./kalag.db", env="DATABASE_URL")
    
    # ===========================================
    # Vector Database (Qdrant) - Optional for dev
    # ===========================================
    qdrant_url: Optional[str] = Field(default=None, env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    qdrant_collection_name: str = "kalag_documents"
    
    # ===========================================
    # AI/LLM (Google Gemini) - Required for full functionality
    # ===========================================
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    # Provider: "aistudio" (Gemini Developer API via API key) or "vertex" (Vertex AI Gemini).
    llm_provider: str = Field(default="aistudio", env="LLM_PROVIDER")

    # Vertex AI config (required when LLM_PROVIDER=vertex)
    gcp_project_id: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    gcp_location: str = Field(default="us-central1", env="GCP_LOCATION")
    # Service account JSON as an env var (recommended for Render). If omitted, uses ADC.
    gcp_service_account_json: Optional[str] = Field(default=None, env="GCP_SERVICE_ACCOUNT_JSON")

    # Model names
    # - AI Studio uses names like "models/gemini-2.5-flash"
    # - Vertex uses names like "gemini-2.0-flash-001" (no "models/" prefix)
    gemini_model: str = Field(default="models/gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_embedding_model: str = Field(default="models/text-embedding-004", env="GEMINI_EMBEDDING_MODEL")

    # Gemini quota safety (optional but recommended in production).
    # These are soft limits enforced via Redis to prevent bursts across
    # the API process and the RQ worker process.
    gemini_generate_requests_per_minute: int = Field(default=20, env="GEMINI_GENERATE_RPM")
    gemini_embed_requests_per_minute: int = Field(default=60, env="GEMINI_EMBED_RPM")

    # Cache (uses Redis when configured)
    query_embedding_cache_ttl_seconds: int = Field(default=7 * 24 * 3600, env="QUERY_EMBED_CACHE_TTL")
    generation_cache_ttl_seconds: int = Field(default=10 * 60, env="GENERATION_CACHE_TTL")
    
    # ===========================================
    # Document Parsing (LlamaParse) - Optional
    # ===========================================
    llama_cloud_api_key: Optional[str] = Field(default=None, env="LLAMA_CLOUD_API_KEY")
    
    # ===========================================
    # File Storage
    # ===========================================
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    @field_validator("upload_dir", mode="before")
    @classmethod
    def _normalize_upload_dir(cls, value):
        # Use an absolute path so that the API process and RQ worker process
        # agree on where files live (they may have different working dirs).
        backend_root = Path(__file__).resolve().parents[1]
        if value is None:
            return str((backend_root / "uploads").resolve())
        path = Path(str(value))
        if not path.is_absolute():
            path = (backend_root / path)
        return str(path.resolve())
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    # ===========================================
    # Rate Limiting
    # ===========================================
    rate_limit_per_minute: int = 60

    # ===========================================
    # Background Job Queue (optional)
    # ===========================================
    # When set, uploads will enqueue document processing jobs instead of running
    # in-process BackgroundTasks. This is recommended for low-tier hosting.
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    queue_name: str = Field(default="kalag", env="QUEUE_NAME")

    # ===========================================
    # Concurrency / Overload Protection
    # ===========================================
    # These caps are PER PROCESS. Keep low on free tiers.
    max_concurrent_document_processes: int = Field(default=1, env="MAX_CONCURRENT_DOCUMENT_PROCESSES")
    max_concurrent_search_requests: int = Field(default=4, env="MAX_CONCURRENT_SEARCH_REQUESTS")
    max_concurrent_llm_requests: int = Field(default=2, env="MAX_CONCURRENT_LLM_REQUESTS")
    max_concurrent_embedding_requests: int = Field(default=2, env="MAX_CONCURRENT_EMBEDDING_REQUESTS")
    # If the server is busy, fail fast rather than hanging.
    busy_timeout_seconds: float = Field(default=0.25, env="BUSY_TIMEOUT_SECONDS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
