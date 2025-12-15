"""Redis helpers used for caching and lightweight rate limiting.

This module is intentionally small and optional:
- If REDIS_URL is not configured, all helpers become no-ops.
- Uses redis-py asyncio client.
"""

from __future__ import annotations

import asyncio
import json
import hashlib
from typing import Any, Optional

from app.config import settings


_redis_lock = asyncio.Lock()
_redis_client = None


async def get_redis():
    """Return a singleton asyncio Redis client or None if not configured."""
    global _redis_client

    if not settings.redis_url:
        return None

    if _redis_client is not None:
        return _redis_client

    async with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        import redis.asyncio as redis

        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        return _redis_client


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def cache_get_json(key: str) -> Optional[Any]:
    client = await get_redis()
    if client is None:
        return None

    raw = await client.get(key)
    if raw is None:
        return None

    try:
        return json.loads(raw)
    except Exception:
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int) -> None:
    client = await get_redis()
    if client is None:
        return

    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    await client.set(key, payload, ex=ttl_seconds)


class UpstreamRateLimitedError(Exception):
    """Raised when our own safety rate-limit is hit."""


async def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> None:
    """Simple fixed-window limiter using Redis INCR.

    This is not meant to be perfect; it prevents bursty spikes from exhausting
    upstream quotas and makes behavior stable across API + worker processes.

    If Redis is not configured, this becomes a no-op.
    """
    if limit <= 0:
        return

    client = await get_redis()
    if client is None:
        return

    # Key should already include a window component to avoid unbounded growth.
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds, nx=True)
    count, _ = await pipe.execute()

    if int(count) > int(limit):
        raise UpstreamRateLimitedError(f"Rate limit exceeded for key={key}")
