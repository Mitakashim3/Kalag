"""
Kalag Embedding Generation
Uses Google Gemini embedding model for vector representations
"""

from typing import List, Optional
import logging

from app.config import settings
from app.utils.concurrency import embedding_semaphore, acquire_or_timeout

logger = logging.getLogger(__name__)

# Try to configure Gemini
_genai_available = False
try:
    import google.generativeai as genai
    from tenacity import retry, stop_after_attempt, wait_exponential
    
    if settings.google_api_key:
        genai.configure(api_key=settings.google_api_key)
        _genai_available = True
        logger.info("Google Generative AI configured")
    else:
        logger.warning("Google API key not set, embeddings disabled")
except ImportError:
    logger.warning("google-generativeai not installed, embeddings disabled")


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for a single text.
    
    Uses Google's text-embedding-004 model which produces
    768-dimensional vectors optimized for semantic similarity.
    
    Args:
        text: Text to embed (max ~2048 tokens)
        
    Returns:
        768-dimensional embedding vector
    """
    if not _genai_available:
        logger.warning("Embeddings disabled, returning empty vector")
        return [0.0] * 768  # Return zero vector as fallback
    
    try:
        import anyio

        def _embed_sync():
            return genai.embed_content(
                model=settings.gemini_embedding_model,
                content=text,
                task_type="retrieval_document"
            )

        async with acquire_or_timeout(embedding_semaphore()):
            result = await anyio.to_thread.run_sync(_embed_sync)
        return result["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    
    Uses retrieval_query task type for better search performance.
    """
    if not _genai_available:
        logger.warning("Embeddings disabled, returning empty vector")
        return [0.0] * 768
    
    try:
        import anyio

        def _embed_sync():
            return genai.embed_content(
                model=settings.gemini_embedding_model,
                content=query,
                task_type="retrieval_query"
            )

        async with acquire_or_timeout(embedding_semaphore()):
            result = await anyio.to_thread.run_sync(_embed_sync)
        return result["embedding"]
    except Exception as e:
        logger.error(f"Query embedding generation failed: {str(e)}")
        raise


async def generate_embeddings_batch(
    texts: List[str],
    batch_size: int = 100
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts efficiently.
    
    Batches requests to stay within rate limits on free tier.
    
    Args:
        texts: List of texts to embed
        batch_size: Max texts per API call
        
    Returns:
        List of embedding vectors in same order as input
    """
    if not _genai_available:
        logger.warning("Embeddings disabled, returning empty vectors")
        return [[0.0] * 768 for _ in texts]
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            import anyio

            def _embed_sync():
                return genai.embed_content(
                    model=settings.gemini_embedding_model,
                    content=batch,
                    task_type="retrieval_document"
                )

            async with acquire_or_timeout(embedding_semaphore()):
                result = await anyio.to_thread.run_sync(_embed_sync)
            all_embeddings.extend(result["embedding"])
        except Exception as e:
            logger.error(f"Batch embedding failed at index {i}: {str(e)}")
            # Fall back to individual embeddings
            for text in batch:
                emb = await generate_embedding(text)
                all_embeddings.append(emb)
    
    return all_embeddings


def get_embedding_dimension() -> int:
    """Return the embedding dimension for Qdrant collection setup."""
    return 768  # text-embedding-004 produces 768-dim vectors
