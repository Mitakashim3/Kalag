"""
Kalag Database Models
SQLAlchemy ORM models for PostgreSQL/SQLite
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    LargeBinary, Float, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class User(Base):
    """
    User model for authentication
    
    Security Considerations:
    - Password is stored as bcrypt hash (never plain text)
    - Email is unique and indexed for fast lookups
    - is_active flag allows soft-disable of accounts
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"


class RefreshToken(Base):
    """
    Refresh Token storage for JWT rotation
    
    Security Considerations:
    - Tokens are stored as hashed values
    - Expires_at allows automatic cleanup
    - Revoked flag for immediate invalidation
    - One user can have multiple active refresh tokens (multi-device)
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_agent = Column(String(512), nullable=True)  # Track device
    ip_address = Column(String(45), nullable=True)  # Track IP (IPv6 max length)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    __table_args__ = (
        Index("ix_refresh_tokens_user_expires", "user_id", "expires_at"),
    )


class Document(Base):
    """
    Uploaded document metadata
    
    Security Considerations:
    - file_path stores relative path, not absolute
    - owner_id ensures document isolation per user
    - Original filename stored separately from stored filename (UUID-based)
    """
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File metadata
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)  # UUID-based for security
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Processing status
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    total_pages = Column(Integer, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_documents_owner_status", "owner_id", "status"),
    )


class DocumentPage(Base):
    """
    Individual page from a document with extracted image
    
    Purpose:
    - Store page images for visual citations
    - Link page numbers to chunks for reference
    - Enable "show me the chart" type queries
    """
    __tablename__ = "document_pages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(512), nullable=False)  # Path to rendered page image
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Vision analysis from Gemini
    vision_description = Column(Text, nullable=True)  # What Gemini sees in the page
    has_charts = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="pages")
    
    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_page"),
        Index("ix_document_pages_doc_page", "document_id", "page_number"),
    )


class DocumentChunk(Base):
    """
    Text chunks from documents for RAG retrieval
    
    Design Decisions:
    - chunk_index preserves order within document
    - page_numbers is comma-separated for chunks spanning pages
    - vector_id references the Qdrant vector store
    - Metadata stored for filtering during retrieval
    """
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    
    # Location reference
    page_numbers = Column(String(100), nullable=True)  # e.g., "5" or "5,6" for spanning chunks
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Vector store reference
    vector_id = Column(String(36), nullable=True)  # ID in Qdrant
    
    # Chunk type for filtering
    chunk_type = Column(String(50), default="text")  # text, table, image_description
    
    # Metadata for retrieval
    token_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    __table_args__ = (
        Index("ix_document_chunks_doc_index", "document_id", "chunk_index"),
        Index("ix_document_chunks_vector", "vector_id"),
    )


class SearchHistory(Base):
    """
    User search history for analytics and improving results
    
    Privacy Note:
    - Can be disabled per user preference
    - Auto-cleaned after retention period
    """
    __tablename__ = "search_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    
    # Metrics
    chunks_retrieved = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Feedback
    was_helpful = Column(Boolean, nullable=True)  # User feedback
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_search_history_user_time", "user_id", "created_at"),
    )
