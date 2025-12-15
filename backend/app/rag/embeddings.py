"""
Kalag Embedding Generation
Uses Google Gemini embedding model for vector representations
"""

from typing import List, Optional
import logging

from app.config import settings
from app.utils.concurrency import embedding_semaphore, acquire_or_timeout
from app.utils.redis_helpers import (
    cache_get_json,
    cache_set_json,
    enforce_rate_limit,
    stable_hash,
    UpstreamRateLimitedError,
)

logger = logging.getLogger(__name__)


def _using_vertex() -> bool:
    return (settings.llm_provider or "").strip().lower() == "vertex"


def _configure_aistudio() -> None:
    import google.generativeai as genai

    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required when LLM_PROVIDER=aistudio")
    genai.configure(api_key=settings.google_api_key)


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
    if not _using_vertex() and not settings.google_api_key:
        logger.warning("Embeddings disabled (no provider credentials), returning empty vector")
        return [0.0] * 768

    # Cache document embeddings too (helps re-processing the same content).
    # Key does not include user_id; embedding depends only on text + model.
    cache_key = f"kalag:emb:doc:{stable_hash(settings.gemini_embedding_model + '|' + text.strip())}"
    cached = await cache_get_json(cache_key)
    if isinstance(cached, list) and len(cached) == 768:
        return [float(x) for x in cached]
    
    try:
        import anyio

        # Soft limit to avoid burning quota via ingestion bursts.
        # Uses a fixed window keyed by minute.
        try:
            from datetime import datetime, timezone

            minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
            await enforce_rate_limit(
                key=f"kalag:rl:gemini:embed:{minute_key}",
                limit=settings.gemini_embed_requests_per_minute,
                window_seconds=60,
            )
        except UpstreamRateLimitedError:
            # Bubble up so routes/jobs can return a 429 instead of hammering upstream.
            raise

        if _using_vertex():
            from app.llm.vertex import embed_text

            async with acquire_or_timeout(embedding_semaphore()):
                embedding = await embed_text(
                    text,
                    settings.gemini_embedding_model,
                    task_type="RETRIEVAL_DOCUMENT",
                )
        else:
            _configure_aistudio()
            import google.generativeai as genai

            def _embed_sync():
                return genai.embed_content(
                    model=settings.gemini_embedding_model,
                    content=text,
                    task_type="retrieval_document",
                )

            async with acquire_or_timeout(embedding_semaphore()):
                result = await anyio.to_thread.run_sync(_embed_sync)
            embedding = result["embedding"]

        await cache_set_json(cache_key, embedding, ttl_seconds=settings.query_embedding_cache_ttl_seconds)
        return embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a search query.
    
    Uses retrieval_query task type for better search performance.
    """
    if not _using_vertex() and not settings.google_api_key:
        logger.warning("Embeddings disabled (no provider credentials), returning empty vector")
        return [0.0] * 768

    normalized = query.strip()
    cache_key = f"kalag:emb:query:{stable_hash(settings.gemini_embedding_model + '|' + normalized)}"
    cached = await cache_get_json(cache_key)
    if isinstance(cached, list) and len(cached) == 768:
        return [float(x) for x in cached]
    
    try:
        import anyio

        try:
            from datetime import datetime, timezone

            minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
            await enforce_rate_limit(
                key=f"kalag:rl:gemini:embed:{minute_key}",
                limit=settings.gemini_embed_requests_per_minute,
                window_seconds=60,
            )
        except UpstreamRateLimitedError:
            raise

        if _using_vertex():
            from app.llm.vertex import embed_text

            async with acquire_or_timeout(embedding_semaphore()):
                embedding = await embed_text(
                    query,
                    settings.gemini_embedding_model,
                    task_type="RETRIEVAL_QUERY",
                )
        else:
            _configure_aistudio()
            import google.generativeai as genai

            def _embed_sync():
                return genai.embed_content(
                    model=settings.gemini_embedding_model,
                    content=query,
                    task_type="retrieval_query",
                )

            async with acquire_or_timeout(embedding_semaphore()):
                result = await anyio.to_thread.run_sync(_embed_sync)
            embedding = result["embedding"]

        await cache_set_json(cache_key, embedding, ttl_seconds=settings.query_embedding_cache_ttl_seconds)
        return embedding
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
    if not _using_vertex() and not settings.google_api_key:
        logger.warning("Embeddings disabled (no provider credentials), returning empty vectors")
        return [[0.0] * 768 for _ in texts]
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            import anyio

            if _using_vertex():
                from app.llm.vertex import embed_texts

                async with acquire_or_timeout(embedding_semaphore()):
                    vectors = await embed_texts(
                        batch,
                        settings.gemini_embedding_model,
                        task_type="RETRIEVAL_DOCUMENT",
                    )
                all_embeddings.extend(vectors)
            else:
                _configure_aistudio()
                import google.generativeai as genai

                def _embed_sync():
                    return genai.embed_content(
                        model=settings.gemini_embedding_model,
                        content=batch,
                        task_type="retrieval_document",
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
