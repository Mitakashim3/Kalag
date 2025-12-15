"""
Kalag Document API Routes
Handles document upload, listing, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
import uuid
import aiofiles
import logging
from pathlib import Path

from app.db.database import get_db
from app.db.models import User, Document, DocumentPage, DocumentChunk
from app.db.schemas import DocumentResponse, DocumentListResponse, DocumentPageResponse
from app.auth import get_current_user
from app.security import limiter, UPLOAD_RATE_LIMIT, sanitize_filename
from app.config import settings
from app.queue import enqueue_document_processing
from app.services.document_processing import process_document
from app.rag import get_vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


def _resolve_possible_upload_path(path_str: str) -> str:
    """Resolve stored paths that may be relative.

    In production the API process and worker process can have different
    working directories. Older rows may also store relative paths.
    """
    if not path_str:
        return path_str

    p = Path(path_str)
    if p.is_absolute():
        return str(p)

    # Try resolving relative to configured upload dir first.
    # Example stored: ./uploads/<user>/<doc>_pages/page_0001.png
    cleaned = path_str.lstrip("./\\")

    # If it starts with uploads/, strip it so we can join to upload_dir.
    if cleaned.startswith("uploads/") or cleaned.startswith("uploads\\"):
        cleaned = cleaned.split("uploads", 1)[1].lstrip("/\\")

    candidates = [
        Path(settings.upload_dir) / cleaned,
        # Also try relative to backend/ and repo root for legacy paths.
        Path(__file__).resolve().parents[3] / path_str.lstrip("./\\"),
        Path(__file__).resolve().parents[4] / path_str.lstrip("./\\"),
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                return str(candidate)
        except Exception:
            continue
    return path_str


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(UPLOAD_RATE_LIMIT)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF document for processing.
    
    Flow:
    1. Validate file type and size
    2. Save file to storage
    3. Create document record
    4. Queue background processing (parse, analyze, embed)
    """
    # Validate file type
    if not file.content_type or file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Generate secure filename
    safe_name = sanitize_filename(file.filename or "document.pdf")
    stored_filename = f"{uuid.uuid4()}_{safe_name}"
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(settings.upload_dir, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, stored_filename)

    # Save file (streaming) + validate file size without loading into memory
    total_bytes = 0
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.max_file_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB",
                    )
                await f.write(chunk)
    except HTTPException:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise
    
    # Create document record
    document = Document(
        owner_id=current_user.id,
        original_filename=safe_name,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=total_bytes,
        mime_type="application/pdf",
        status="pending"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Queue background processing
    # Prefer Redis-backed queue when configured to keep the web process stable.
    try:
        job_id = await enqueue_document_processing(
            document_id=str(document.id),
            user_id=str(current_user.id),
        )
    except Exception:
        job_id = None

    if job_id is None:
        background_tasks.add_task(
            process_document,
            document_id=str(document.id),
            user_id=str(current_user.id),
        )
    
    return document


"""NOTE:
The heavy document processing pipeline lives in app.services.document_processing.
We keep this router focused on HTTP concerns.
"""


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's documents with pagination."""
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id))
        .where(Document.owner_id == current_user.id)
    )
    total = count_result.scalar()
    
    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.owner_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document and its vectors."""
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .where(Document.owner_id == current_user.id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from vector store
    vector_store = get_vector_store()
    await vector_store.delete_document(document_id, current_user.id)
    
    # Delete file
    try:
        os.remove(document.file_path)
    except:
        pass
    
    # Delete pages directory
    pages_dir = os.path.join(
        settings.upload_dir,
        current_user.id,
        f"{document_id}_pages"
    )
    try:
        import shutil
        shutil.rmtree(pages_dir)
    except:
        pass
    
    # Delete database record (cascades to chunks and pages)
    await db.delete(document)
    await db.commit()


@router.get("/{document_id}/pages/{page_number}/image")
async def get_page_image(
    document_id: str,
    page_number: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the rendered image for a specific page.
    Used for visual citations in search results.
    """
    # Verify ownership
    result = await db.execute(
        select(DocumentPage)
        .join(Document)
        .where(DocumentPage.document_id == document_id)
        .where(DocumentPage.page_number == page_number)
        .where(Document.owner_id == current_user.id)
    )
    page = result.scalar_one_or_none()
    
    if not page:
        logger.warning(f"Page not found in database: document={document_id}, page={page_number}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found. Document may still be processing."
        )
    
    resolved_path = _resolve_possible_upload_path(page.image_path)
    if not resolved_path or not os.path.exists(resolved_path):
        logger.warning(f"Image file not found on disk: {page.image_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page image not available. Document may still be processing."
        )
    
    return FileResponse(
        resolved_path,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=3600"}
    )
