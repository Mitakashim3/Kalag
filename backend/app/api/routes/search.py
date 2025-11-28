"""
Kalag Search API Routes
RAG-powered search with visual citations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import time

from app.db.database import get_db
from app.db.models import User, SearchHistory
from app.db.schemas import SearchQuery, SearchResponse, Citation
from app.auth import get_current_user
from app.security import limiter, SEARCH_RATE_LIMIT, sanitize_search_query, PromptInjectionError
from app.rag import Retriever, generate_answer

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
@limiter.limit(SEARCH_RATE_LIMIT)
async def search_documents(
    request: Request,
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search across user's documents using RAG.
    
    Flow:
    1. Sanitize query for security (prevent prompt injection)
    2. Retrieve relevant chunks from vector store
    3. Generate answer using Gemini with retrieved context
    4. Return answer with visual citations
    
    Visual Citations:
    - Each citation includes page number and optional image URL
    - Frontend can display the relevant document section
    """
    import logging
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    
    try:
        # Sanitize query
        safe_query = sanitize_search_query(query.query)
        logger.info(f"Search query: {safe_query}")
    except PromptInjectionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query detected. Please rephrase your question."
        )
    
    # Initialize retriever
    retriever = Retriever(db)
    
    # Retrieve relevant chunks
    results = await retriever.retrieve(
        query=safe_query,
        user_id=current_user.id,
        top_k=query.top_k,
        document_ids=query.document_ids,
        include_images=query.include_images
    )
    
    logger.info(f"Retrieved {len(results)} results for user {current_user.id}")
    for i, r in enumerate(results[:3]):  # Log first 3 results
        logger.info(f"Result {i}: score={r.get('relevance_score')}, page={r.get('page_number')}, content_preview={r.get('content', '')[:100]}")
    
    if not results:
        return SearchResponse(
            answer="I couldn't find any relevant information in your documents for this query.",
            citations=[],
            query=query.query,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    # Build context for generation
    if hasattr(retriever, '_format_context'):
        context = retriever._format_context(results)
    else:
        context_parts = []
        for r in results:
            part = f"[{r['document_name']}, Page {r.get('page_number', 'N/A')}]: {r['content']}"
            if r.get("image_url"):
                # Let the model know a supporting visual exists so it can describe it
                visual_tags = []
                if r.get("page_has_charts"):
                    visual_tags.append("chart")
                if r.get("page_has_tables"):
                    visual_tags.append("table")
                tags_text = f" ({', '.join(visual_tags)})" if visual_tags else ""
                part += f"\nVISUAL_REFERENCE{tags_text}: An image for this page is available via the citation viewer. Describe what it shows when relevant."
            context_parts.append(part)
        context = "\n\n".join(context_parts)
    
    # Build citations
    citations = [
        Citation(
            document_id=r["document_id"],
            document_name=r["document_name"],
            page_number=r.get("page_number", 0),
            chunk_content=r["content"][:1000],  # Increased limit for better context display
            relevance_score=r["relevance_score"],
            image_url=r.get("image_url")
        )
        for r in results
    ]
    
    # Generate answer
    generation_result = await generate_answer(
        query=safe_query,
        context=context,
        citations=[c.model_dump() for c in citations]
    )
    
    # Handle blocked responses (prompt injection detected)
    if generation_result.get("blocked"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=generation_result["answer"]
        )
    
    processing_time_ms = int((time.time() - start_time) * 1000)
    
    # Log search for analytics (optional)
    search_log = SearchHistory(
        user_id=current_user.id,
        query=query.query,
        response=generation_result["answer"][:1000],
        chunks_retrieved=len(results),
        response_time_ms=processing_time_ms
    )
    db.add(search_log)
    # Don't await - fire and forget for analytics
    
    return SearchResponse(
        answer=generation_result["answer"],
        citations=citations,
        query=query.query,
        processing_time_ms=processing_time_ms
    )


@router.post("/visual", response_model=SearchResponse)
@limiter.limit(SEARCH_RATE_LIMIT)
async def search_with_visual_context(
    request: Request,
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search with enhanced visual context.
    
    When querying about charts, graphs, or visual elements,
    this endpoint passes the page image to Gemini for better answers.
    
    Example query: "What is the Q3 revenue shown in the chart on page 5?"
    """
    from app.rag import generate_with_vision
    from sqlalchemy import select
    from app.db.models import DocumentPage
    
    start_time = time.time()
    
    try:
        safe_query = sanitize_search_query(query.query)
    except PromptInjectionError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid query detected."
        )
    
    # Retrieve relevant chunks
    retriever = Retriever(db)
    results = await retriever.retrieve(
        query=safe_query,
        user_id=current_user.id,
        top_k=query.top_k,
        document_ids=query.document_ids,
        include_images=True
    )
    
    if not results:
        return SearchResponse(
            answer="No relevant information found.",
            citations=[],
            query=query.query,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    # Find pages with visual content
    visual_results = [r for r in results if r.get("page_has_charts") or r.get("page_has_tables")]
    
    # Get the most relevant page image
    page_image_path = None
    if visual_results:
        top_visual = visual_results[0]
        page_result = await db.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == top_visual["document_id"])
            .where(DocumentPage.page_number == top_visual["page_number"])
        )
        page = page_result.scalar_one_or_none()
        if page:
            page_image_path = page.image_path
    
    # Build context
    context = "\n\n".join(
        f"[{r['document_name']}, Page {r.get('page_number', 'N/A')}]: {r['content']}"
        for r in results
    )
    
    # Generate with vision
    answer = await generate_with_vision(
        query=safe_query,
        context=context,
        page_image_path=page_image_path
    )
    
    # Build citations
    citations = [
        Citation(
            document_id=r["document_id"],
            document_name=r["document_name"],
            page_number=r.get("page_number", 0),
            chunk_content=r["content"][:500],
            relevance_score=r["relevance_score"],
            image_url=r.get("image_url")
        )
        for r in results
    ]
    
    return SearchResponse(
        answer=answer,
        citations=citations,
        query=query.query,
        processing_time_ms=int((time.time() - start_time) * 1000)
    )
