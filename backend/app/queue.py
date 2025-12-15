"""Queue integration.

Uses Redis + RQ when REDIS_URL is configured.

Design goal: keep the FastAPI web process lightweight by enqueueing heavy
document ingestion work to a separate worker process.
"""

from __future__ import annotations

from typing import Optional

import anyio
from redis import Redis
from rq import Queue

from app.config import settings
from app.worker_jobs import process_document_job


def _get_redis() -> Redis:
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL not configured")
    return Redis.from_url(settings.redis_url)


def _get_queue() -> Queue:
    return Queue(name=settings.queue_name, connection=_get_redis())


async def enqueue_document_processing(document_id: str, user_id: str) -> Optional[str]:
    """Enqueue document processing and return the job id.

    Returns None if queue is not configured.
    """

    if not settings.redis_url or not settings.enable_queue:
        return None

    def _enqueue() -> str:
        q = _get_queue()
        job = q.enqueue(
            process_document_job,
            document_id,
            user_id,
            # Large PDFs + LLM calls can be slow.
            job_timeout=60 * 20,
            result_ttl=0,
        )
        return job.id

    return await anyio.to_thread.run_sync(_enqueue)
