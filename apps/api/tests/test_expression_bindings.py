"""Tests for the workflow-wide JSONata bindings (PR10): `$trigger`, `$vars`,
`$env`, `$secrets`, `$loop`.

These give users JSONata-mode equivalents of the legacy `{{trigger.x}}` /
`{{variables.x}}` / `{{env.X}}` / `{{secrets.X}}` / `{{loop.x}}` namespaces.
"""

from __future__ import annotations

from apps.api.app.execution_engine.engine.expression_engine import JsonataResolver


def test_trigger_binding_resolves() -> None:
    resolver = JsonataResolver(trigger_data={"url": "https://example.com", "method": "POST"})
    assert resolver.evaluate("$trigger.url") == "https://example.com"
    assert resolver.evaluate("$trigger.method") == "POST"


def test_vars_binding_resolves() -> None:
    resolver = JsonataResolver(variables={"count": 7, "name": "Ada"})
    assert resolver.evaluate("$vars.count") == 7
    assert resolver.evaluate("$vars.name") == "Ada"


def test_env_binding_resolves() -> None:
    resolver = JsonataResolver(env={"API_URL": "https://api.fuse.io"})
    assert resolver.evaluate("$env.API_URL") == "https://api.fuse.io"


def test_secrets_binding_resolves() -> None:
    resolver = JsonataResolver(secrets={"DB_PASSWORD": "hunter2"})
    assert resolver.evaluate("$secrets.DB_PASSWORD") == "hunter2"


def test_loop_binding_resolves() -> None:
    resolver = JsonataResolver(
        loop_data={"item": {"id": 9}, "index": 2, "total": 5},
    )
    assert resolver.evaluate("$loop.item.id") == 9
    assert resolver.evaluate("$loop.index") == 2


def test_bindings_default_to_empty_dict() -> None:
    resolver = JsonataResolver()
    # Missing paths cleanly return None — they don't raise.
    assert resolver.evaluate("$trigger.x") is None
    assert resolver.evaluate("$vars.x") is None
    assert resolver.evaluate("$env.X") is None
    assert resolver.evaluate("$secrets.X") is None
    assert resolver.evaluate("$loop.x") is None


def test_bindings_compose_with_arithmetic_and_sugar() -> None:
    resolver = JsonataResolver(
        trigger_data={"count": 3},
        variables={"multiplier": 4},
    )
    assert resolver.evaluate("$trigger.count * $vars.multiplier") == 12


def test_explicit_bindings_still_override() -> None:
    resolver = JsonataResolver(trigger_data={"x": 1})
    # Caller-passed bindings win over the built-in trigger binding.
    assert resolver.evaluate("$trigger.x", bindings={"trigger": {"x": 999}}) == 999
