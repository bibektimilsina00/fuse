"""Health check endpoint for monitoring and container orchestration."""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, text
from src.database import engine

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthStatus(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str = "1.0.0"
    checks: Dict[str, Any]


class ServiceCheck(BaseModel):
    """Individual service check result."""

    status: str
    latency_ms: float | None = None
    error: str | None = None


def check_database() -> ServiceCheck:
    """Check database connectivity."""
    import time

    start = time.time()
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        return ServiceCheck(status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return ServiceCheck(status="unhealthy", error=str(e))


def check_redis() -> ServiceCheck:
    """Check Redis connectivity."""
    import time

    start = time.time()
    try:
        from src.utils.redis_client import redis_client

        redis_client.ping()
        latency = (time.time() - start) * 1000
        return ServiceCheck(status="healthy", latency_ms=round(latency, 2))
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return ServiceCheck(status="unhealthy", error=str(e))


@router.get("/health", response_model=HealthStatus, tags=["system"])
def health_check() -> HealthStatus:
    """
    Health check endpoint for monitoring and container orchestration.

    Returns the health status of the application and its dependencies:
    - Database connectivity
    - Redis connectivity

    Use this endpoint for:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring dashboards
    """
    db_check = check_database()
    redis_check = check_redis()

    # Overall status is unhealthy if any critical service is down
    overall_status = "healthy"
    if db_check.status == "unhealthy":
        overall_status = "unhealthy"
    elif redis_check.status == "unhealthy":
        overall_status = "degraded"  # Redis is optional for basic operation

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        checks={
            "database": db_check.model_dump(),
            "redis": redis_check.model_dump(),
        },
    )


@router.get("/health/live", tags=["system"])
def liveness_probe() -> Dict[str, str]:
    """
    Simple liveness probe for Kubernetes.
    Returns 200 if the application is running.
    """
    return {"status": "alive"}


@router.get("/health/ready", tags=["system"])
def readiness_probe() -> Dict[str, str]:
    """
    Readiness probe for Kubernetes.
    Returns 200 only if all critical services are available.
    """
    db_check = check_database()
    if db_check.status == "unhealthy":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database unavailable")

    return {"status": "ready"}


@router.get("/health/circuit-breakers", tags=["system"])
def circuit_breaker_status() -> Dict[str, Any]:
    """
    Get status of all circuit breakers.

    Returns statistics for each circuit breaker including:
    - Current state (closed, open, half_open)
    - Failure count
    - Success count
    - Total calls
    """
    from src.utils.circuit_breaker import get_circuit_breaker_stats

    stats = get_circuit_breaker_stats()
    return {
        "circuit_breakers": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/feature-flags", tags=["system"])
def feature_flags_status() -> Dict[str, Any]:
    """
    Get status of all feature flags.

    Returns configuration for each feature flag including:
    - Name and description
    - Enabled status
    - Rollout strategy
    - Percentage (for percentage rollout)
    """
    from src.utils.feature_flags import FeatureFlags

    flags = FeatureFlags.get_all_flags()
    return {
        "feature_flags": flags,
        "timestamp": datetime.utcnow().isoformat(),
    }
