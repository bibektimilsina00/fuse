"""
Caching utilities using Redis.

Provides decorators and utilities for caching expensive operations
like database queries, external API calls, and computed results.
"""

import functools
import hashlib
import json
import logging
import os
from typing import Any, Callable, Optional, TypeVar, Union

from fuse.utils.redis_client import async_redis_client, redis_client

logger = logging.getLogger("fuse_backend")

# Disable caching in development mode
DISABLE_CACHE = os.getenv("DISABLE_CACHE", "false").lower() in ("true", "1", "yes") or os.getenv("ENV", "development") == "development"

# Type variable for generic return types
T = TypeVar("T")


# Default cache TTLs (in seconds)
class CacheTTL:
    """Standard cache TTL values."""

    SHORT = 60  # 1 minute - for frequently changing data
    MEDIUM = 300  # 5 minutes - for semi-static data
    LONG = 3600  # 1 hour - for static data
    NODE_TYPES = 60  # 1 minute - reduced for development
    WORKFLOW_META = 300  # Workflow metadata
    USER_SESSION = 86400  # 24 hours


def make_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Generate a consistent cache key from function arguments.

    Args:
        prefix: Cache key prefix (usually function name)
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        A unique cache key string
    """
    # Create a deterministic string from args/kwargs
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
    return f"cache:{prefix}:{key_hash}"


def cache(
    ttl: int = CacheTTL.MEDIUM,
    prefix: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching synchronous function results in Redis.

    Args:
        ttl: Time-to-live in seconds
        prefix: Custom cache key prefix (defaults to function name)
        key_builder: Custom function to build cache key

    Example:
        @cache(ttl=CacheTTL.LONG)
        def get_node_types():
            return expensive_db_query()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Bypass cache in development mode
            if DISABLE_CACHE:
                return func(*args, **kwargs)
            
            # Build cache key
            cache_prefix = prefix or func.__name__
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(cache_prefix, *args, **kwargs)

            try:
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Cache miss - execute function
            result = func(*args, **kwargs)

            try:
                # Store in cache
                redis_client.setex(cache_key, ttl, json.dumps(result, default=str))
                logger.debug(f"Cache set: {cache_key} (ttl={ttl}s)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result

        return wrapper

    return decorator


from typing import Awaitable

F = TypeVar("F", bound=Callable[..., Any])


def async_cache(
    ttl: int = CacheTTL.MEDIUM,
    prefix: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable[[F], F]:
    """
    Decorator for caching async function results in Redis.

    Example:
        @async_cache(ttl=CacheTTL.SHORT)
        async def fetch_user_workflows(user_id: str):
            return await db.query(...)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Bypass cache in development mode
            if DISABLE_CACHE:
                return await func(*args, **kwargs)
            
            # Build cache key
            cache_prefix = prefix or func.__name__
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(cache_prefix, *args, **kwargs)

            try:
                # Try to get from cache
                cached = await async_redis_client.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            try:
                # Store in cache
                await async_redis_client.setex(
                    cache_key, ttl, json.dumps(result, default=str)
                )
                logger.debug(f"Cache set: {cache_key} (ttl={ttl}s)")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "cache:get_node_types:*")

    Returns:
        Number of keys deleted
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            count = redis_client.delete(*keys)
            logger.info(f"Invalidated {count} cache entries matching {pattern}")
            return count
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")
        return 0


async def async_invalidate_cache(pattern: str) -> int:
    """
    Async version of cache invalidation.

    Args:
        pattern: Redis key pattern

    Returns:
        Number of keys deleted
    """
    try:
        keys = await async_redis_client.keys(pattern)
        if keys:
            count = await async_redis_client.delete(*keys)
            logger.info(f"Invalidated {count} cache entries matching {pattern}")
            return count
        return 0
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")
        return 0


# Specific cache invalidation helpers
def invalidate_node_types_cache() -> int:
    """Invalidate all node types cache entries."""
    return invalidate_cache("cache:get_node_types:*") + invalidate_cache(
        "cache:node_types:*"
    )


def invalidate_workflow_cache(workflow_id: str) -> int:
    """Invalidate cache for a specific workflow."""
    return invalidate_cache(f"cache:*workflow*:{workflow_id}*")


def invalidate_user_cache(user_id: str) -> int:
    """Invalidate all cache entries for a user."""
    return invalidate_cache(f"cache:*:{user_id}*")
