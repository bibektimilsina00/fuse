"""
Request ID middleware for distributed tracing.

Generates a unique request ID for each incoming request and:
1. Adds it to the request state for access in route handlers
2. Includes it in all log messages via contextvars
3. Returns it in response headers (X-Request-ID)
4. Supports client-provided request IDs via X-Request-ID header
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request ID - accessible anywhere in the request lifecycle
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Header names
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_var.get()


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a unique request ID to each request.

    Features:
    - Generates UUID v4 request IDs
    - Accepts client-provided X-Request-ID headers
    - Accepts X-Correlation-ID for distributed tracing chains
    - Makes request ID available via contextvars for logging
    - Adds request ID to response headers
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check for client-provided request ID or correlation ID
        request_id = (
            request.headers.get(REQUEST_ID_HEADER)
            or request.headers.get(CORRELATION_ID_HEADER)
            or generate_request_id()
        )

        # Store in context variable for logging and other uses
        token = request_id_var.set(request_id)

        # Also store in request state for easy access in route handlers
        request.state.request_id = request_id

        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers[REQUEST_ID_HEADER] = request_id

            return response
        finally:
            # Reset context variable
            request_id_var.reset(token)


# Helper function for logging with request ID
def get_log_context() -> dict:
    """
    Get logging context with request ID.
    Use this when creating log records to include request tracing.

    Example:
        logger.info("Processing request", extra=get_log_context())
    """
    request_id = get_request_id()
    if request_id:
        return {"request_id": request_id}
    return {}
