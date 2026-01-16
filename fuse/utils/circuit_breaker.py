"""
Circuit breaker pattern implementation for external service calls.

The circuit breaker prevents cascading failures by:
1. Tracking failures to external services
2. "Opening" the circuit when failure threshold is reached
3. Allowing the circuit to "half-open" after a recovery timeout
4. "Closing" the circuit when successful calls resume

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit is broken, requests fail immediately
- HALF_OPEN: Testing if service has recovered
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Successes needed to close from half-open
    timeout: float = 30.0  # Seconds before trying half-open
    window_size: int = 60  # Seconds to track failures

    @classmethod
    def get_default_timeout(cls) -> float:
        from fuse.config import settings
        if settings.ENVIRONMENT == "local":
            return 5.0  # Faster recovery in dev
        return 30.0


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=100))
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for protecting against external service failures.

    Usage:
        breaker = CircuitBreaker("openai-api")

        async def call_openai():
            async with breaker:
                return await openai_client.chat.completions.create(...)
    """

    _instances: Dict[str, "CircuitBreaker"] = {}

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @classmethod
    def get_or_create(
        cls,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> "CircuitBreaker":
        """Get an existing circuit breaker or create a new one."""
        if name not in cls._instances:
            cls._instances[name] = cls(name, config)
        return cls._instances[name]

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {
            name: {
                "state": cb.stats.state.value,
                "failure_count": cb.stats.failure_count,
                "success_count": cb.stats.success_count,
                "total_calls": cb.stats.total_calls,
                "total_failures": cb.stats.total_failures,
                "total_successes": cb.stats.total_successes,
            }
            for name, cb in cls._instances.items()
        }

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state, checking for timeout transition."""
        if self.stats.state == CircuitState.OPEN:
            if time.time() - self.stats.last_state_change >= self.config.timeout:
                return CircuitState.HALF_OPEN
        return self.stats.state

    def _clean_old_failures(self) -> None:
        """Remove failures outside the tracking window."""
        cutoff = time.time() - self.config.window_size
        while self.stats.recent_failures and self.stats.recent_failures[0] < cutoff:
            self.stats.recent_failures.popleft()
            self.stats.failure_count = max(0, self.stats.failure_count - 1)

    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.total_calls += 1

            current_state = self.state

            if current_state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(f"Circuit breaker '{self.name}' closed after recovery")

    async def _record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            self._clean_old_failures()

            now = time.time()
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.total_calls += 1
            self.stats.last_failure_time = now
            self.stats.recent_failures.append(now)

            current_state = self.state

            if current_state == CircuitState.HALF_OPEN:
                # Single failure in half-open reopens the circuit
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit breaker '{self.name}' reopened after failure in half-open state: {error}"
                )
            elif current_state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.warning(
                        f"Circuit breaker '{self.name}' opened after {self.stats.failure_count} failures"
                    )

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        self.stats.state = new_state
        self.stats.last_state_change = time.time()

        if new_state == CircuitState.CLOSED:
            self.stats.failure_count = 0
            self.stats.success_count = 0
            self.stats.recent_failures.clear()
        elif new_state == CircuitState.HALF_OPEN:
            self.stats.success_count = 0

    def is_available(self) -> bool:
        """Check if the circuit breaker allows requests."""
        return self.state != CircuitState.OPEN

    async def __aenter__(self) -> "CircuitBreaker":
        """Enter the circuit breaker context."""
        if self.state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting request")
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open, service unavailable"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit the circuit breaker context."""
        if exc_type is None:
            await self._record_success()
        else:
            # Don't open circuit for rate limits in dev
            is_rate_limit = False
            err_str = str(exc_val).lower()
            if "429" in err_str or "rate limit" in err_str:
                is_rate_limit = True

            from fuse.config import settings
            if settings.ENVIRONMENT == "local" and is_rate_limit:
                # Still count as a call but don't count towards opening the circuit
                async with self._lock:
                    self.stats.total_calls += 1
                return False

            await self._record_failure(exc_val)
        return False  # Don't suppress the exception


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open and rejecting requests."""

    pass


# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 30.0,
) -> Callable[[F], F]:
    """
    Decorator to wrap a function with circuit breaker protection.

    Usage:
        @circuit_breaker("openai-api")
        async def call_openai():
            return await client.chat.completions.create(...)

    Args:
        name: Unique name for this circuit breaker
        failure_threshold: Number of failures before opening
        success_threshold: Successes needed to close from half-open
        timeout: Seconds before trying half-open
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout,
    )
    breaker = CircuitBreaker.get_or_create(name, config)

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with breaker:
                return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


# Pre-configured circuit breakers for common services
class CircuitBreakers:
    """Pre-configured circuit breakers for common external services."""

    @staticmethod
    def openai() -> CircuitBreaker:
        """Circuit breaker for OpenAI API calls."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            "openai-api",
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 3,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 60.0,
            ),
        )

    @staticmethod
    def anthropic() -> CircuitBreaker:
        """Circuit breaker for Anthropic API calls."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            "anthropic-api",
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 3,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 60.0,
            ),
        )

    @staticmethod
    def slack() -> CircuitBreaker:
        """Circuit breaker for Slack API calls."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            "slack-api",
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 5,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 30.0,
            ),
        )

    @staticmethod
    def discord() -> CircuitBreaker:
        """Circuit breaker for Discord API calls."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            "discord-api",
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 5,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 30.0,
            ),
        )

    @staticmethod
    def google() -> CircuitBreaker:
        """Circuit breaker for Google API calls (Sheets, etc.)."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            "google-api",
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 5,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 30.0,
            ),
        )

    @staticmethod
    def http(name: str = "http-default") -> CircuitBreaker:
        """Circuit breaker for generic HTTP calls."""
        from fuse.config import settings
        return CircuitBreaker.get_or_create(
            name,
            CircuitBreakerConfig(
                failure_threshold=10 if settings.ENVIRONMENT == "local" else 5,
                success_threshold=2,
                timeout=5.0 if settings.ENVIRONMENT == "local" else 30.0,
            ),
        )


# Convenience function for getting stats via API
def get_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all circuit breakers."""
    return CircuitBreaker.get_all_stats()
