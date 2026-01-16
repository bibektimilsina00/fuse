import redis
import redis.asyncio as aioredis
from fuse.config import settings

# Async Redis Client for FastAPI (WebSockets)
async_redis_client = aioredis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)

# Sync Redis Client for Celery Tasks
sync_redis_client = redis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)

# Alias for backward compatibility
redis_client = sync_redis_client


def get_redis_client():
    return sync_redis_client
