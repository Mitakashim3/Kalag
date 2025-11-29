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
from app.ingestion import (
    DocumentParser, render_pdf_pages, analyze_page_image,
    batch_analyze_pages, TextChunker
)
from app.rag import generate_embeddings_batch, get_vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


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
    
    # Read and validate file size
    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.max_file_size_mb}MB"
        )
    
    # Generate secure filename
    safe_name = sanitize_filename(file.filename or "document.pdf")
    stored_filename = f"{uuid.uuid4()}_{safe_name}"
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(settings.upload_dir, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, stored_filename)
    
    # Save file
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    
    # Create document record
    document = Document(
        owner_id=current_user.id,
        original_filename=safe_name,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=len(contents),
        mime_type="application/pdf",
        status="pending"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Queue background processing
    background_tasks.add_task(
        process_document,
        document_id=str(document.id),
        user_id=str(current_user.id)
    )
    
    return document


async def process_document(document_id: str, user_id: str):
    """
    Background task to process uploaded document.
    
    Steps:
    1. Parse PDF with LlamaParse
    2. Render pages to images
    3. Analyze each page with Gemini Vision
    4. Chunk text content
    5. Generate embeddings
    6. Store in Qdrant
    """
    from app.db.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                return
            
            # Update status
            document.status = "processing"
            await db.commit()
            
            # Step 1: Parse PDF
            parser = DocumentParser()
            parsed = await parser.parse_pdf(document.file_path)
            document.total_pages = parsed["total_pages"]
            
            # Step 2: Render pages to images for vision analysis
            pages_dir = os.path.join(
                settings.upload_dir,
                str(user_id),
                f"{str(document_id)}_pages"
            )
            page_images = await render_pdf_pages(document.file_path, pages_dir)
            
            # Step 3: Analyze pages with vision
            image_paths = [p["image_path"] for p in page_images]
            vision_results = await batch_analyze_pages(image_paths, concurrency=2)
            
            # Save page records
            for page_info, vision_result in zip(page_images, vision_results):
                page = DocumentPage(
                    document_id=document_id,
                    page_number=page_info["page_number"],
                    image_path=page_info["image_path"],
                    width=page_info["width"],
                    height=page_info["height"],
                    vision_description=vision_result.get("description"),
                    has_charts=vision_result.get("has_charts", False),
                    has_tables=vision_result.get("has_tables", False),
                    has_images=vision_result.get("has_images", False)
                )
                db.add(page)
            
            # Step 4: Chunk text content
            chunker = TextChunker()
            
            # Chunk parsed text
            text_chunks = chunker.chunk_with_pages(parsed["pages"])
            
            # Also create chunks from vision descriptions
            vision_chunks = []
            for page_info, vision_result in zip(page_images, vision_results):
                if vision_result.get("description"):
                    vision_chunks.append({
                        "content": vision_result["description"],
                        "page_number": page_info["page_number"],
                        "chunk_type": "image_description",
                        "chunk_index": len(text_chunks) + len(vision_chunks)
                    })
            
            all_chunks = text_chunks + vision_chunks
            
            # Step 5: Generate embeddings
            chunk_texts = [c["content"] for c in all_chunks]
            embeddings = await generate_embeddings_batch(chunk_texts)
            
            # Step 6: Store in Qdrant
            vector_store = get_vector_store()
            vector_ids = await vector_store.upsert_chunks(
                chunks=all_chunks,
                embeddings=embeddings,
                user_id=str(user_id),
                document_id=str(document_id)
            )
            
            # Save chunk records
            for chunk, vector_id in zip(all_chunks, vector_ids):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    page_numbers=str(chunk.get("page_number", "")),
                    chunk_type=chunk.get("chunk_type", "text"),
                    vector_id=vector_id,
                    token_count=len(chunk["content"]) // 4
                )
                db.add(chunk_record)
            
            # Mark as completed
            document.status = "completed"
            document.processed_at = func.now()
            await db.commit()
            
        except Exception as e:
            # Mark as failed
            document.status = "failed"
            document.processing_error = str(e)
            await db.commit()
            raise


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
    
    if not page or not os.path.exists(page.image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page image not found"
        )
    
    return FileResponse(
        page.image_path,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=3600"}
    )
