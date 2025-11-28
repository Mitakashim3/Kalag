"""
Kalag RAG Retriever
Retrieves relevant chunks with visual citations
"""

from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.rag.vectorstore import get_vector_store
from app.rag.embeddings import generate_query_embedding
from app.db.models import Document, DocumentPage, DocumentChunk
from app.security.sanitizer import sanitize_search_query

logger = logging.getLogger(__name__)


class Retriever:
    """
    RAG Retriever with visual citation support.
    
    This retriever:
    1. Sanitizes queries for security
    2. Generates query embeddings
    3. Searches vector store
    4. Enriches results with document metadata and page images
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_store = get_vector_store()
    
    async def retrieve(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        include_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks with visual citations.
        
        Args:
            query: User's search query
            user_id: Current user ID
            top_k: Number of results
            document_ids: Optional document filter
            include_images: Whether to include page image URLs
            
        Returns:
            List of enriched results with citations
        """
        # Sanitize query for security
        safe_query = sanitize_search_query(query)
        
        # Generate query embedding
        query_embedding = await generate_query_embedding(safe_query)
        
        # Search vector store
        raw_results = await self.vector_store.search(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=top_k,
            document_ids=document_ids
        )
        
        if not raw_results:
            return []
        
        # Enrich results with document info and images
        enriched_results = await self._enrich_results(
            raw_results,
            include_images=include_images
        )
        
        return enriched_results
    
    async def _enrich_results(
        self,
        results: List[Dict[str, Any]],
        include_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enrich search results with document metadata and page images.
        """
        enriched = []
        
        # Collect unique document IDs
        doc_ids = list(set(r["document_id"] for r in results if r.get("document_id")))
        
        # Fetch documents
        doc_query = await self.db.execute(
            select(Document).where(Document.id.in_(doc_ids))
        )
        documents = {doc.id: doc for doc in doc_query.scalars().all()}
        
        # Fetch page images if needed
        page_images = {}
        if include_images:
            page_query = await self.db.execute(
                select(DocumentPage).where(DocumentPage.document_id.in_(doc_ids))
            )
            for page in page_query.scalars().all():
                key = (page.document_id, page.page_number)
                page_images[key] = page
        
        for result in results:
            doc = documents.get(result["document_id"])
            
            enriched_result = {
                "content": result["content"],
                "relevance_score": result["score"],
                "document_id": result["document_id"],
                "document_name": doc.original_filename if doc else "Unknown",
                "page_number": result.get("page_number"),
                "chunk_type": result.get("chunk_type", "text"),
                "image_url": None
            }
            
            # Add page image if available
            if include_images and result.get("page_number"):
                page_key = (result["document_id"], result["page_number"])
                page = page_images.get(page_key)
                if page:
                    # In production, this would be a presigned URL or CDN URL
                    enriched_result["image_url"] = f"/api/documents/{result['document_id']}/pages/{result['page_number']}/image"
                    enriched_result["page_has_charts"] = page.has_charts
                    enriched_result["page_has_tables"] = page.has_tables
            
            enriched.append(enriched_result)
        
        return enriched
    
    async def retrieve_for_context(
        self,
        query: str,
        user_id: str,
        max_tokens: int = 4000
    ) -> str:
        """
        Retrieve and format chunks for LLM context.
        
        Respects token limits for the generation step.
        """
        results = await self.retrieve(
            query=query,
            user_id=user_id,
            top_k=10,
            include_images=False
        )
        
        context_parts = []
        total_tokens = 0
        
        for result in results:
            chunk_text = f"[Source: {result['document_name']}, Page {result.get('page_number', 'N/A')}]\n{result['content']}\n"
            chunk_tokens = len(chunk_text) // 4  # Rough estimate
            
            if total_tokens + chunk_tokens > max_tokens:
                break
            
            context_parts.append(chunk_text)
            total_tokens += chunk_tokens
        
        return "\n---\n".join(context_parts)
