"""Unit tests for the Redis-backed tool rate limiter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.app.node_system.tools.rate_limit import (
    RateLimitPolicy,
    RatePolicy_default,
    RedisRateLimiter,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _ctx(workspace_id: str = "ws_1"):
    return MagicMock(workspace_id=workspace_id)


# ── Policy ─────────────────────────────────────────────────────────


def test_policy_default_resolution():
    p = RateLimitPolicy(default_limit=60, default_window_seconds=60)
    assert p.resolve("ws_1", "anything") == (60, 60)


def test_policy_per_tool_wins_over_workspace():
    p = RateLimitPolicy(default_limit=60, default_window_seconds=60)
    p.set_workspace_limit("ws_1", limit=200, window_seconds=60)
    p.set_tool_limit("slack_send_message", limit=30, window_seconds=60)
    assert p.resolve("ws_1", "slack_send_message") == (30, 60)


def test_policy_workspace_falls_through_when_no_tool_override():
    p = RateLimitPolicy()
    p.set_workspace_limit("ws_vip", limit=500, window_seconds=60)
    assert p.resolve("ws_vip", "any_tool") == (500, 60)


def test_policy_rejects_invalid_values():
    p = RateLimitPolicy()
    with pytest.raises(ValueError):
        p.set_tool_limit("x", limit=0)
    with pytest.raises(ValueError):
        p.set_workspace_limit("x", limit=-1)


def test_default_policy_caps_known_expensive_tools():
    p = RatePolicy_default()
    assert p.resolve("ws_1", "slack_send_message")[0] == 30
    assert p.resolve("ws_1", "openai_image_generate")[0] == 10


# ── Limiter ────────────────────────────────────────────────────────


class _FakeRedis:
    """Minimal Redis stub that tracks INCR/EXPIRE per key for tests."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, ttl: int) -> None:
        self.ttls[key] = ttl


@pytest.mark.anyio
async def test_limiter_allows_until_bucket_full():
    policy = RateLimitPolicy(default_limit=3, default_window_seconds=60)
    fake = _FakeRedis()
    limiter = RedisRateLimiter(policy, time_fn=lambda: 1_700_000_000)

    with patch(
        "apps.api.app.node_system.tools.rate_limit.get_redis",
        new=AsyncMock(return_value=fake),
    ):
        allows = [await limiter.check("ws_1", "tool_x", _ctx()) for _ in range(5)]

    # First 3 allowed, next 2 denied.
    assert allows == [True, True, True, False, False]
    # TTL set exactly once (on first INCR).
    assert len(fake.ttls) == 1
    assert next(iter(fake.ttls.values())) == 60


@pytest.mark.anyio
async def test_limiter_uses_per_tool_override():
    policy = RateLimitPolicy(default_limit=100, default_window_seconds=60)
    policy.set_tool_limit("expensive", limit=1, window_seconds=60)
    fake = _FakeRedis()
    limiter = RedisRateLimiter(policy, time_fn=lambda: 1_700_000_000)

    with patch(
        "apps.api.app.node_system.tools.rate_limit.get_redis",
        new=AsyncMock(return_value=fake),
    ):
        first = await limiter.check("ws_1", "expensive", _ctx())
        second = await limiter.check("ws_1", "expensive", _ctx())
    assert (first, second) == (True, False)


@pytest.mark.anyio
async def test_limiter_separate_buckets_per_workspace():
    policy = RateLimitPolicy(default_limit=1, default_window_seconds=60)
    fake = _FakeRedis()
    limiter = RedisRateLimiter(policy, time_fn=lambda: 1_700_000_000)

    with patch(
        "apps.api.app.node_system.tools.rate_limit.get_redis",
        new=AsyncMock(return_value=fake),
    ):
        a = await limiter.check("ws_a", "tool_x", _ctx("ws_a"))
        b = await limiter.check("ws_b", "tool_x", _ctx("ws_b"))
    assert (a, b) == (True, True)  # Workspaces are isolated.


@pytest.mark.anyio
async def test_limiter_fails_open_on_redis_error():
    policy = RateLimitPolicy(default_limit=1, default_window_seconds=60)
    limiter = RedisRateLimiter(policy, time_fn=lambda: 1_700_000_000)

    with patch(
        "apps.api.app.node_system.tools.rate_limit.get_redis",
        new=AsyncMock(side_effect=RuntimeError("redis dead")),
    ):
        allowed = await limiter.check("ws_x", "tool_y", _ctx())
    # Fail-open so a Redis blip doesn't take every loop down.
    assert allowed is True


@pytest.mark.anyio
async def test_limiter_window_rolls_over_at_bucket_boundary():
    policy = RateLimitPolicy(default_limit=1, default_window_seconds=10)
    fake = _FakeRedis()
    times = iter([100.0, 100.5, 110.0])  # 1st + 2nd in bucket 10, 3rd in bucket 11
    limiter = RedisRateLimiter(policy, time_fn=lambda: next(times))

    with patch(
        "apps.api.app.node_system.tools.rate_limit.get_redis",
        new=AsyncMock(return_value=fake),
    ):
        first = await limiter.check("ws_1", "t", _ctx())
        second = await limiter.check("ws_1", "t", _ctx())
        third = await limiter.check("ws_1", "t", _ctx())
    assert (first, second, third) == (True, False, True)
