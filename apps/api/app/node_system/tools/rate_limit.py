"""Redis-backed per-(workspace, tool) rate limiter for the tool registry.

Wires into the hook ``ToolRegistry.set_rate_limit_check`` exposed by
Phase 4 (PR #219). Strategy: fixed-window counter per
``(workspace_id, tool_id, window_seconds_bucket)``. Cheap (one INCR
+ optional EXPIRE), good enough for agent-loop throttling — we are
not trying to prevent a coordinated burst, just stop one runaway
loop from melting through a quota.

Configuration:
- ``DEFAULT_LIMIT`` / ``DEFAULT_WINDOW_SECONDS`` cover every tool that
  doesn't have a specific override.
- ``per_tool_overrides`` lets ops dial down a known-expensive tool
  (e.g. an image-generation tool) without touching the rest.
- Workspaces are not exempted; ops can pre-set a high count in
  ``ws_overrides`` for trusted internal workspaces.

The limiter is intentionally fail-open: any Redis error returns
``True`` (allow) and logs. A loop that runs because Redis blipped is
strictly better than every loop in every workspace failing.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

from apps.api.app.core.redis import get_redis
from apps.api.app.node_system.base.node_context import NodeContext

logger = logging.getLogger(__name__)


KEY_PREFIX = "runmycrew:toolrl"


@dataclass
class RateLimitPolicy:
    """How many calls per window are allowed for one (workspace, tool) pair.

    A fresh policy can be constructed empty and incrementally populated
    via ``set_tool_limit`` / ``set_workspace_limit`` at app startup —
    that's how the production wiring loads operator overrides without
    a deploy.
    """

    default_limit: int = 60
    default_window_seconds: int = 60
    per_tool_overrides: dict[str, tuple[int, int]] = field(default_factory=dict)
    """``tool_id → (limit, window_seconds)``."""

    ws_overrides: dict[str, tuple[int, int]] = field(default_factory=dict)
    """``workspace_id → (limit, window_seconds)`` — workspace-wide bump."""

    def set_tool_limit(self, tool_id: str, *, limit: int, window_seconds: int = 60) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.per_tool_overrides[tool_id] = (limit, window_seconds)

    def set_workspace_limit(
        self, workspace_id: str, *, limit: int, window_seconds: int = 60
    ) -> None:
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self.ws_overrides[workspace_id] = (limit, window_seconds)

    def resolve(self, workspace_id: str, tool_id: str) -> tuple[int, int]:
        """Pick the most-specific (limit, window) for the request.

        Order: per-tool > per-workspace > default. Per-tool wins because
        an expensive tool is expensive regardless of the workspace.
        """
        if tool_id in self.per_tool_overrides:
            return self.per_tool_overrides[tool_id]
        if workspace_id and workspace_id in self.ws_overrides:
            return self.ws_overrides[workspace_id]
        return self.default_limit, self.default_window_seconds


class RedisRateLimiter:
    """Fixed-window counter against Redis.

    Bucket key: ``runmycrew:toolrl:{workspace_id}:{tool_id}:{bucket}``
    where ``bucket = floor(now / window_seconds)``. We INCR, then on the
    first hit set the TTL to ``window_seconds`` so the key reaps itself.
    """

    def __init__(self, policy: RateLimitPolicy, *, time_fn: Any = time.time) -> None:
        self.policy = policy
        self._time = time_fn

    async def check(self, workspace_id: str, tool_id: str, ctx: NodeContext) -> bool:
        """Hook signature matches ``ToolRegistry.RateLimitCheck``.

        Returns True when the call is allowed; False when the bucket is
        full. Allows on any Redis error (fail-open).
        """
        limit, window_seconds = self.policy.resolve(workspace_id, tool_id)
        try:
            redis = await get_redis()
        except Exception as exc:  # pragma: no cover — exercised in prod only
            logger.warning("rate_limit: redis unavailable, failing open: %s", exc)
            return True

        bucket = int(math.floor(self._time() / window_seconds))
        key = f"{KEY_PREFIX}:{workspace_id or 'anon'}:{tool_id}:{bucket}"
        try:
            new_count = await redis.incr(key)
            if new_count == 1:
                # Only set TTL on the first INCR — saves a round-trip
                # on the hot path.
                await redis.expire(key, window_seconds)
        except Exception as exc:
            logger.warning("rate_limit: incr failed, failing open: %s", exc)
            return True
        return new_count <= limit


# ── Wiring ─────────────────────────────────────────────────────────


_active_limiter: RedisRateLimiter | None = None


def install_default_rate_limiter(policy: RateLimitPolicy | None = None) -> RedisRateLimiter:
    """Bind a Redis-backed limiter to the global ``tool_registry``.

    Called from app startup. Replacing the limiter mid-flight is safe —
    in-flight calls finish against the previous limiter; new calls hit
    the new one.
    """
    from apps.api.app.node_system.tools.registry import tool_registry

    global _active_limiter
    limiter = RedisRateLimiter(policy or RatePolicy_default())
    # The ``set_rate_limit_check`` method is added by Phase 4 (PR #219).
    # Defensive lookup keeps imports working on branches that haven't
    # picked up that change yet — the limiter just stays unwired.
    setter = getattr(tool_registry, "set_rate_limit_check", None)
    if setter is None:
        logger.warning(
            "rate_limit: tool_registry has no set_rate_limit_check hook "
            "(Phase 4 not merged?); limiter NOT wired"
        )
        return limiter
    setter(limiter.check)
    _active_limiter = limiter
    return limiter


def get_active_limiter() -> RedisRateLimiter | None:
    """Return the currently-installed limiter (None if not wired)."""
    return _active_limiter


def RatePolicy_default() -> RateLimitPolicy:
    """Default policy used when ``install_default_rate_limiter`` is
    called without an explicit policy.

    Sets conservative ceilings on the few tools that are known to be
    expensive or rate-limited upstream. Everything else gets the
    60-calls-per-minute default.
    """
    p = RateLimitPolicy(default_limit=60, default_window_seconds=60)
    # Slack rate-limits at ~1 message/sec per channel; cap our agent loops
    # well below that to avoid 429s blowing through retries.
    p.set_tool_limit("slack_send_message", limit=30, window_seconds=60)
    # OpenAI image generation is paid per call and slow; a runaway loop
    # would burn through quota in seconds without this.
    p.set_tool_limit("openai_image_generate", limit=10, window_seconds=60)
    return p
