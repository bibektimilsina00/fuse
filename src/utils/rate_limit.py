"""Rate limiting middleware using Redis for distributed rate limiting."""

import logging
import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from src.utils.redis_client import redis_client
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limiting configuration."""

    # Default limits (requests per window)
    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60  # seconds

    # Per-endpoint limits (path pattern -> (limit, window))
    ENDPOINT_LIMITS = {
        "/api/v1/workflows/ai": (20, 60),  # AI endpoints are expensive
        "/api/v1/auth/login": (10, 60),  # Prevent brute force
        "/api/v1/workflows/webhooks": (200, 60),  # Higher limit for webhooks
    }

    # Exempt paths (no rate limiting)
    EXEMPT_PATHS = {
        "/health",
        "/health/live",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }


def get_rate_limit_key(request: Request) -> str:
    """
    Generate a unique key for rate limiting.
    Uses IP address and optionally user ID for authenticated requests.
    """
    # Get client IP (handle X-Forwarded-For for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Include user ID if authenticated
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"rate_limit:{user_id}:{request.url.path}"

    return f"rate_limit:{client_ip}:{request.url.path}"


def get_limit_for_path(path: str) -> tuple[int, int]:
    """Get rate limit and window for a given path."""
    for pattern, (limit, window) in RateLimitConfig.ENDPOINT_LIMITS.items():
        if path.startswith(pattern):
            return limit, window
    return RateLimitConfig.DEFAULT_LIMIT, RateLimitConfig.DEFAULT_WINDOW


def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, dict]:
    """
    Check if request is within rate limit using Redis sliding window.

    Returns:
        (allowed, info) where info contains remaining, reset time, etc.
    """
    try:
        current_time = int(time.time())
        window_start = current_time - window

        pipe = redis_client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request with timestamp as score
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiry on the key
        pipe.expire(key, window)

        results = pipe.execute()
        request_count = results[1]

        remaining = max(0, limit - request_count - 1)
        reset_time = current_time + window

        info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "window": window,
        }

        return request_count < limit, info

    except Exception as e:
        logger.warning(f"Rate limit check failed (allowing request): {e}")
        # On Redis failure, allow the request but log the error
        return True, {"limit": limit, "remaining": limit, "reset": 0, "window": window}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window algorithm.

    Adds rate limit headers to responses:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining in window
    - X-RateLimit-Reset: Unix timestamp when window resets
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for local development
        from src.config import settings
        if settings.ENVIRONMENT == "local":
            return await call_next(request)

        # Skip rate limiting for exempt paths
        if request.url.path in RateLimitConfig.EXEMPT_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get rate limit configuration for this path
        limit, window = get_limit_for_path(request.url.path)

        # Generate rate limit key
        key = get_rate_limit_key(request)

        # Check rate limit
        allowed, info = check_rate_limit(key, limit, window)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {key}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["window"]),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response
