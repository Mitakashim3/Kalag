import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from app.config import settings


_document_semaphore: Optional[asyncio.Semaphore] = None
_search_semaphore: Optional[asyncio.Semaphore] = None
_llm_semaphore: Optional[asyncio.Semaphore] = None
_embedding_semaphore: Optional[asyncio.Semaphore] = None


def document_semaphore() -> asyncio.Semaphore:
    global _document_semaphore
    if _document_semaphore is None:
        _document_semaphore = asyncio.Semaphore(settings.max_concurrent_document_processes)
    return _document_semaphore


def search_semaphore() -> asyncio.Semaphore:
    global _search_semaphore
    if _search_semaphore is None:
        _search_semaphore = asyncio.Semaphore(settings.max_concurrent_search_requests)
    return _search_semaphore


def llm_semaphore() -> asyncio.Semaphore:
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(settings.max_concurrent_llm_requests)
    return _llm_semaphore


def embedding_semaphore() -> asyncio.Semaphore:
    global _embedding_semaphore
    if _embedding_semaphore is None:
        _embedding_semaphore = asyncio.Semaphore(settings.max_concurrent_embedding_requests)
    return _embedding_semaphore


@asynccontextmanager
async def acquire_or_timeout(
    semaphore: asyncio.Semaphore,
    *,
    timeout_seconds: Optional[float] = None,
) -> AsyncIterator[None]:
    """Acquire a semaphore with a short timeout to avoid hanging under load."""
    timeout = settings.busy_timeout_seconds if timeout_seconds is None else timeout_seconds
    acquired = False
    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=timeout)
        acquired = True
        yield
    finally:
        if acquired:
            semaphore.release()
