"""
Kalag Pydantic Schemas
Request/Response validation models
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ===========================================
# Auth Schemas
# ===========================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response for login - access_token in body, refresh_token in cookie"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiry


class RefreshResponse(BaseModel):
    """Response for token refresh"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ===========================================
# Document Schemas
# ===========================================

class DocumentBase(BaseModel):
    original_filename: str


class DocumentResponse(DocumentBase):
    id: str
    status: str
    total_pages: Optional[int]
    file_size_bytes: int
    mime_type: str
    created_at: datetime
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class DocumentPageResponse(BaseModel):
    id: str
    page_number: int
    image_url: str  # Presigned URL or path
    has_charts: bool
    has_tables: bool
    has_images: bool
    vision_description: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


# ===========================================
# Search Schemas
# ===========================================

class SearchQuery(BaseModel):
    """Search request with security sanitization"""
    query: str = Field(..., min_length=1, max_length=1000)
    document_ids: Optional[List[str]] = None  # Filter to specific documents
    include_images: bool = True  # Include visual citations
    top_k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    """A single source citation"""
    document_id: str
    document_name: str
    page_number: int
    chunk_content: str
    relevance_score: float
    image_url: Optional[str] = None  # URL to page image crop


class SearchResponse(BaseModel):
    """Search response with answer and citations"""
    answer: str
    citations: List[Citation]
    query: str
    processing_time_ms: int


# ===========================================
# Error Schemas
# ===========================================

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    detail: List[dict]
