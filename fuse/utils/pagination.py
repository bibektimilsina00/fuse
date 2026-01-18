"""Pagination utilities with proper guards."""

from typing import Annotated

from fastapi import Query

# Pagination constants
MAX_LIMIT = 1000  # Maximum items per page
DEFAULT_LIMIT = 100  # Default items per page
MIN_SKIP = 0  # Minimum skip value


def validate_pagination(skip: int = 0, limit: int = DEFAULT_LIMIT) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        skip: Number of items to skip (must be >= 0)
        limit: Maximum items to return (capped at MAX_LIMIT)

    Returns:
        Tuple of (validated_skip, validated_limit)
    """
    validated_skip = max(MIN_SKIP, skip)
    validated_limit = min(max(1, limit), MAX_LIMIT)
    return validated_skip, validated_limit


# FastAPI dependency for validated pagination
PaginationSkip = Annotated[
    int, Query(ge=0, description="Number of items to skip", examples=[0])
]

PaginationLimit = Annotated[
    int,
    Query(
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of items to return (max: {MAX_LIMIT})",
        examples=[DEFAULT_LIMIT],
    ),
]
