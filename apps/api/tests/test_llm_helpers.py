"""Unit tests for the LLM action node's secret-redaction helper."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.ai.llm.llm import _redact_secrets


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Google generativelanguage style
        (
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyABC123",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=***",
        ),
        # `api_key` variant
        (
            "https://example.com/v1/chat?api_key=sk-abc123",
            "https://example.com/v1/chat?api_key=***",
        ),
        # `api-key` variant
        (
            "https://example.com/v1/chat?api-key=sk-abc123",
            "https://example.com/v1/chat?api-key=***",
        ),
        # `access_token` variant
        (
            "https://example.com/oauth?access_token=ya29.abc",
            "https://example.com/oauth?access_token=***",
        ),
        # `token` variant
        (
            "https://example.com/v1/foo?token=abcdef&other=ok",
            "https://example.com/v1/foo?token=***&other=ok",
        ),
        # Case-insensitive — uppercase param name
        (
            "https://example.com/v1/foo?KEY=abcdef",
            "https://example.com/v1/foo?KEY=***",
        ),
        # Key appears after another param
        (
            "https://example.com/v1/foo?other=ok&key=secret",
            "https://example.com/v1/foo?other=ok&key=***",
        ),
        # Multiple secret-like params — strip both
        (
            "https://example.com/v1?key=K1&token=T1",
            "https://example.com/v1?key=***&token=***",
        ),
        # No secret-like param — leave URL alone
        (
            "https://api.openai.com/v1/chat/completions",
            "https://api.openai.com/v1/chat/completions",
        ),
        # URL with only path — passthrough
        ("https://example.com/path", "https://example.com/path"),
    ],
)
def test_redact_secrets(raw, expected):
    assert _redact_secrets(raw) == expected
