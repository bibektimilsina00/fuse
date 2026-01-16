import logging

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fuse.api import api_router
from fuse.config import settings
from fuse.logger import setup_global_logger
from fuse.utils.health import router as health_router
from fuse.utils.rate_limit import RateLimitMiddleware
from fuse.utils.request_id import RequestIDMiddleware
from starlette.middleware.cors import CORSMiddleware

# Setup global logger (available as 'logger' everywhere)
setup_global_logger()

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)


# Log validation errors for debugging
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.error(f"Validation error for {request.url}: {errors}")
    return JSONResponse(status_code=422, content={"detail": errors})


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Rate limiting middleware (add after CORS to ensure CORS headers are set)
app.add_middleware(RateLimitMiddleware)

# Request ID middleware for distributed tracing
app.add_middleware(RequestIDMiddleware)

# Health check endpoints (no prefix, accessible at /health)
app.include_router(health_router)

app.include_router(api_router, prefix=settings.API_V1_STR)

import os
from pathlib import Path

from fastapi.responses import FileResponse

# Serve static frontend files (must be last to not override API routes)
from fastapi.staticfiles import StaticFiles

static_dir = Path(__file__).parent / "static"

if static_dir.exists():
    logger.info(f"Serving frontend from: {static_dir}")

    # Mount static files
    app.mount("/assets", StaticFiles(directory=static_dir), name="static")

    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend application for all non-API routes."""
        # If path starts with api/v1, it should have been handled by API router
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # Serve index.html for SPA routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})

else:
    logger.warning(f"Static frontend directory not found at: {static_dir}")
    logger.warning("Run 'scripts/build_frontend.sh' to build and bundle the frontend")
