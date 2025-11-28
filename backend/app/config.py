"""
Kalag Backend Configuration
Centralized configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ===========================================
    # Application
    # ===========================================
    app_name: str = "Kalag"
    debug: bool = True
    
    # ===========================================
    # Security & Auth
    # ===========================================
    secret_key: str = Field(default="dev-secret-key-change-in-production-12345", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Cookie Settings
    cookie_domain: str = "localhost"
    cookie_secure: bool = False  # True in production
    cookie_samesite: str = "lax"
    
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
    gemini_model: str = "models/gemini-2.5-flash"  # Faster and more quota-friendly
    gemini_embedding_model: str = "models/text-embedding-004"
    
    # ===========================================
    # Document Parsing (LlamaParse) - Optional
    # ===========================================
    llama_cloud_api_key: Optional[str] = Field(default=None, env="LLAMA_CLOUD_API_KEY")
    
    # ===========================================
    # File Storage
    # ===========================================
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024
    
    # ===========================================
    # Rate Limiting
    # ===========================================
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
