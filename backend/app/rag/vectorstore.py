"""
Kalag Vector Store
Qdrant Cloud integration for semantic search
"""

from typing import List, Dict, Any, Optional
import logging
import uuid

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Qdrant client
_qdrant_available = False
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue
    )
    _qdrant_available = True
except ImportError:
    logger.warning("Qdrant client not available")


def get_embedding_dimension() -> int:
    """Get embedding dimension (768 for text-embedding-004)."""
    return 768


class VectorStore:
    """
    Qdrant vector store for document chunks.
    
    Optimized for:
    - Free tier limits (1GB)
    - Fast similarity search
    - Metadata filtering (by user, document)
    """
    
    def __init__(self):
        self.enabled = (
            _qdrant_available 
            and settings.qdrant_url is not None 
            and settings.qdrant_api_key is not None
        )
        
        if self.enabled:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30
            )
            self.collection_name = settings.qdrant_collection_name
            logger.info("Qdrant vector store enabled")
        else:
            self.client = None
            self.collection_name = None
            logger.warning("Qdrant not configured - vector search disabled")
    
    async def initialize(self):
        """
        Initialize the Qdrant collection if it doesn't exist.
        Call this on app startup.
        """
        if not self.enabled:
            logger.info("Skipping Qdrant initialization (not configured)")
            return
        
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=get_embedding_dimension(),
                    distance=Distance.COSINE
                ),
                # Optimize for free tier
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=10000,  # Delay indexing for small datasets
                ),
                # Enable payload indexing for filtering
                on_disk_payload=True
            )
            
            # Create payload indexes for efficient filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        else:
            logger.info(f"Qdrant collection already exists: {self.collection_name}")
    
    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        user_id: str,
        document_id: str
    ) -> List[str]:
        """
        Insert or update document chunks with their embeddings.
        
        Args:
            chunks: List of chunk dicts with content and metadata
            embeddings: Corresponding embedding vectors
            user_id: Owner user ID for filtering
            document_id: Parent document ID
            
        Returns:
            List of vector IDs
        """
        if not self.enabled:
            logger.warning("Vector store not enabled, skipping upsert")
            return []
        
        points = []
        vector_ids = []
        
        for chunk, embedding in zip(chunks, embeddings):
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            points.append(PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    "user_id": user_id,
                    "document_id": document_id,
                    "content": chunk["content"],
                    "chunk_index": chunk.get("chunk_index", 0),
                    "page_number": chunk.get("page_number"),
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "start_char": chunk.get("start_char"),
                    "end_char": chunk.get("end_char"),
                }
            ))
        
        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        
        logger.info(f"Upserted {len(points)} chunks for document {document_id}")
        return vector_ids
    
    async def search(
        self,
        query_embedding: List[float],
        user_id: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        score_threshold: float = 0.3  # Lowered from 0.5 for better recall
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        CRITICAL: Always filters by user_id to ensure data isolation.
        
        Args:
            query_embedding: Query vector
            user_id: Current user ID (required for security)
            top_k: Number of results
            document_ids: Optional filter to specific documents
            score_threshold: Minimum similarity score
            
        Returns:
            List of matching chunks with scores
        """
        if not self.enabled:
            logger.warning("Vector store not enabled, returning empty results")
            return []
        
        # Build filter - ALWAYS include user_id
        must_conditions = [
            FieldCondition(
                key="user_id",
                match=MatchValue(value=user_id)
            )
        ]
        
        # Optional document filter
        if document_ids:
            must_conditions.append(
                FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=document_ids)
                )
            )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(must=must_conditions),
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True
        )
        
        return [
            {
                "vector_id": str(r.id),
                "score": r.score,
                "content": r.payload.get("content", ""),
                "document_id": r.payload.get("document_id"),
                "page_number": r.payload.get("page_number"),
                "chunk_type": r.payload.get("chunk_type"),
                "chunk_index": r.payload.get("chunk_index"),
            }
            for r in results
        ]
    
    async def delete_document(self, document_id: str, user_id: str):
        """
        Delete all chunks for a document.
        
        
        Args:
            document_id: Document to delete
            user_id: Owner verification (security)
        """
        if not self.enabled:
            logger.warning("Vector store not enabled, skipping delete")
            return
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        ),
                        FieldCondition(
                            key="user_id",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
        )
        logger.info(f"Deleted vectors for document {document_id}")
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics for monitoring."""
        if not self.enabled:
            return {"vectors_count": 0, "points_count": 0, "status": "disabled"}
        
        info = self.client.get_collection(self.collection_name)
        return {
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status
        }


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
