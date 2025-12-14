"""Document processing pipeline.

This module is intentionally framework-agnostic so it can be used from:
- FastAPI BackgroundTasks (in-process)
- A separate queue worker process (recommended for production)
"""

from __future__ import annotations

import logging
import os

from sqlalchemy import select, func, update

from app.config import settings
from app.db.database import AsyncSessionLocal
from app.db.models import Document, DocumentChunk, DocumentPage
from app.ingestion import DocumentParser, render_pdf_pages, batch_analyze_pages, TextChunker
from app.rag import generate_embeddings_batch, get_vector_store
from app.utils.concurrency import document_semaphore


logger = logging.getLogger(__name__)


async def process_document(document_id: str, user_id: str) -> None:
    """Process an uploaded document.

    Safe to call multiple times; will no-op if the document is already
    processing or completed.
    """

    sem = document_semaphore()
    await sem.acquire()
    try:
        async with AsyncSessionLocal() as db:
            # Atomically claim the document for processing to avoid double-work
            claimed = False
            try:
                claim_result = await db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .where(Document.owner_id == user_id)
                    .where(Document.status.in_(["pending"]))
                    .values(status="processing")
                    .returning(Document.id)
                    .execution_options(synchronize_session=False)
                )
                claimed = claim_result.scalar_one_or_none() is not None
            except Exception:
                # Fallback for dialects without RETURNING support.
                claim_result = await db.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .where(Document.owner_id == user_id)
                    .where(Document.status.in_(["pending"]))
                    .values(status="processing")
                    .execution_options(synchronize_session=False)
                )
                claimed = bool(getattr(claim_result, "rowcount", 0) == 1)

            if not claimed:
                # Already processed, processing, missing, or not owned by user.
                return

            # Load the document after claim
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document:
                return

            # Commit the status change early so the UI can reflect "processing"
            # and so other workers won't re-claim it.
            await db.commit()

            # Step 1: Parse PDF
            parser = DocumentParser()
            parsed = await parser.parse_pdf(document.file_path)
            document.total_pages = parsed["total_pages"]

            # Step 2: Render pages to images for vision analysis
            pages_dir = os.path.join(settings.upload_dir, str(user_id), f"{str(document_id)}_pages")
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
                    has_images=vision_result.get("has_images", False),
                )
                db.add(page)

            # Step 4: Chunk text content
            chunker = TextChunker()
            text_chunks = chunker.chunk_with_pages(parsed["pages"])

            vision_chunks = []
            for page_info, vision_result in zip(page_images, vision_results):
                if vision_result.get("description"):
                    vision_chunks.append(
                        {
                            "content": vision_result["description"],
                            "page_number": page_info["page_number"],
                            "chunk_type": "image_description",
                            "chunk_index": len(text_chunks) + len(vision_chunks),
                        }
                    )

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
                document_id=str(document_id),
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
                    token_count=len(chunk["content"]) // 4,
                )
                db.add(chunk_record)

            # Mark as completed
            document.status = "completed"
            document.processed_at = func.now()
            await db.commit()

    except Exception as e:
        # Mark as failed and log the error
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Document).where(Document.id == document_id))
                document = result.scalar_one_or_none()
                if document:
                    document.status = "failed"
                    document.processing_error = str(e)
                    await db.commit()
        except Exception:
            # Best-effort failure marking
            pass

        logger.error(f"Document processing failed for {document_id}: {str(e)}", exc_info=True)
    finally:
        sem.release()
