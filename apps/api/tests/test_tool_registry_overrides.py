"""Tests for the per-call credential pinning and retry override in
`ToolRegistry.execute` (PR 4.5).

The agent passes `credential_id=` and `retry_override=` to scope which
workspace credential the tool should consume and to swap the retry config
the inspector configured. These tests cover the registry behaviour
directly; the agent-side plumbing is covered by manual smoke + the typed
caller signature.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from apps.api.app.node_system.tools.base import (
    ToolDefinition,
    ToolOAuth,
    ToolParam,
    ToolResult,
    ToolRetryConfig,
)
from apps.api.app.node_system.tools.registry import ToolRegistry


def _ctx(creds: list[dict[str, Any]] | None = None) -> Any:
    """Cheap NodeContext-ish stand-in. The registry only reads
    `context.credentials` so we don't need the full plumbing."""
    return SimpleNamespace(credentials=creds or [], variables={})


# ──────────────────────────────────────────────────────────────────────────
#  Credential pinning
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_credential_id_pinning_selects_specific_credential() -> None:
    registry = ToolRegistry()
    captured: dict[str, Any] = {}

    async def fake_exec(params: dict[str, Any], _ctx: Any) -> ToolResult:
        captured.update(params)
        return ToolResult(success=True, output={})

    registry.register(
        ToolDefinition(
            id="needs_auth",
            name="Needs Auth",
            description="",
            params={},
            oauth=ToolOAuth(required=True, credential_type="slack_oauth"),
        ),
        fake_exec,
    )

    creds = [
        {"id": "cred-a", "type": "slack_oauth", "data": {"access_token": "token-a"}},
        {"id": "cred-b", "type": "slack_oauth", "data": {"access_token": "token-b"}},
    ]

    result = await registry.execute("needs_auth", {}, _ctx(creds), credential_id="cred-b")
    assert result.success
    assert captured["_oauth_token"] == "token-b"


@pytest.mark.anyio
async def test_credential_id_unset_falls_back_to_first_match() -> None:
    registry = ToolRegistry()
    captured: dict[str, Any] = {}

    async def fake_exec(params: dict[str, Any], _ctx: Any) -> ToolResult:
        captured.update(params)
        return ToolResult(success=True, output={})

    registry.register(
        ToolDefinition(
            id="needs_auth",
            name="Needs Auth",
            description="",
            params={"channel": ToolParam(type="string")},
            oauth=ToolOAuth(required=True, credential_type="slack_oauth"),
        ),
        fake_exec,
    )

    creds = [
        {"id": "cred-a", "type": "slack_oauth", "data": {"access_token": "first"}},
        {"id": "cred-b", "type": "slack_oauth", "data": {"access_token": "second"}},
    ]
    result = await registry.execute("needs_auth", {}, _ctx(creds))
    assert result.success
    # First credential of matching type wins when no id is pinned — the
    # legacy behaviour that existing workflows rely on.
    assert captured["_oauth_token"] == "first"


@pytest.mark.anyio
async def test_credential_id_pinning_to_missing_id_fails() -> None:
    registry = ToolRegistry()

    async def fake_exec(_params: dict[str, Any], _ctx: Any) -> ToolResult:
        return ToolResult(success=True, output={})

    registry.register(
        ToolDefinition(
            id="needs_auth",
            name="Needs Auth",
            description="",
            params={},
            oauth=ToolOAuth(required=True, credential_type="slack_oauth"),
        ),
        fake_exec,
    )

    creds = [{"id": "cred-a", "type": "slack_oauth", "data": {"access_token": "t"}}]
    result = await registry.execute("needs_auth", {}, _ctx(creds), credential_id="cred-z")
    assert not result.success
    assert "Credential 'slack_oauth' not found" in (result.error or "")


# ──────────────────────────────────────────────────────────────────────────
#  Retry override
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_retry_override_replaces_built_in_config() -> None:
    registry = ToolRegistry()
    attempts = 0

    async def flaky(_p: dict[str, Any], _c: Any) -> ToolResult:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return ToolResult(success=False, error="boom")
        return ToolResult(success=True, output={"attempt": attempts})

    # Built-in retry is disabled — the tool would normally try once and
    # give up. The override forces three attempts so it succeeds.
    registry.register(
        ToolDefinition(
            id="flaky",
            name="Flaky",
            description="",
            params={},
            retry=ToolRetryConfig(enabled=False),
        ),
        flaky,
    )

    result = await registry.execute(
        "flaky",
        {},
        _ctx(),
        retry_override=ToolRetryConfig(
            enabled=True, max_retries=5, initial_delay_ms=0, max_delay_ms=0
        ),
    )
    assert result.success
    assert attempts == 3


@pytest.mark.anyio
async def test_retry_override_disabled_when_built_in_was_enabled() -> None:
    registry = ToolRegistry()
    attempts = 0

    async def always_fails(_p: dict[str, Any], _c: Any) -> ToolResult:
        nonlocal attempts
        attempts += 1
        return ToolResult(success=False, error="nope")

    registry.register(
        ToolDefinition(
            id="bad",
            name="Bad",
            description="",
            params={},
            # Tool default would attempt 4 times — override forces 1.
            retry=ToolRetryConfig(enabled=True, max_retries=3, initial_delay_ms=0, max_delay_ms=0),
        ),
        always_fails,
    )

    result = await registry.execute(
        "bad",
        {},
        _ctx(),
        retry_override=ToolRetryConfig(enabled=False),
    )
    assert not result.success
    assert attempts == 1


@pytest.mark.anyio
async def test_no_override_uses_built_in_retry() -> None:
    registry = ToolRegistry()
    attempts = 0

    async def flaky(_p: dict[str, Any], _c: Any) -> ToolResult:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            return ToolResult(success=False, error="boom")
        return ToolResult(success=True, output={})

    registry.register(
        ToolDefinition(
            id="flaky",
            name="Flaky",
            description="",
            params={},
            retry=ToolRetryConfig(enabled=True, max_retries=3, initial_delay_ms=0, max_delay_ms=0),
        ),
        flaky,
    )

    result = await registry.execute("flaky", {}, _ctx())
    assert result.success
    assert attempts == 2


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


# Sanity check that `asyncio` is imported and reachable — keeps lint happy
# in case the helper above is the only user.
def test_asyncio_module_is_importable() -> None:
    assert asyncio is not None
