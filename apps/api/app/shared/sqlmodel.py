from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel


class SQLModelBase(SQLModel):
    """Base class for SQLModel-backed feature models."""


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Datetime column that always stores and returns timezone-aware UTC values.

    Maps to ``TIMESTAMP WITH TIME ZONE`` so asyncpg binds tz-aware datetimes
    (which ``utc_now`` produces) without coercion errors.
    """

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def created_at_field() -> Any:
    """A non-null ``created_at`` column defaulting to the current UTC time."""
    return Field(
        default_factory=utc_now,
        sa_column=Column(UTCDateTime(), nullable=False, default=utc_now),
    )


def updated_at_field() -> Any:
    """A non-null ``updated_at`` column that refreshes to UTC now on update."""
    return Field(
        default_factory=utc_now,
        sa_column=Column(UTCDateTime(), nullable=False, default=utc_now, onupdate=utc_now),
    )
