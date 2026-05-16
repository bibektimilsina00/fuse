import asyncio

import redis.asyncio as aioredis

from apps.api.app.core.config import settings

_redis_pool: aioredis.Redis | None = None
_redis_loop: asyncio.AbstractEventLoop | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_loop, _redis_pool
    current_loop = asyncio.get_running_loop()
    if _redis_pool is None or _redis_loop != current_loop:
        if _redis_pool is not None and _redis_loop == current_loop:
            await _redis_pool.aclose()
        _redis_pool = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
        )
        _redis_loop = current_loop
    return _redis_pool


async def close_redis() -> None:
    global _redis_loop, _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
        _redis_loop = None
