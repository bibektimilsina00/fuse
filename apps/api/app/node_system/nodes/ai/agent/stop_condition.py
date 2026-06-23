"""Declarative stop-condition evaluation for agent loops.

Users supply a JSONata expression on the agent node's
``success_when`` field. After every iteration the runtime parses the
agent's final response and evaluates the expression against it. A
truthy result means the loop is done; a falsy result tells the LLM
to keep going.

We use pure-Python ``jsonata`` to avoid pulling node-side eval. If
the expression is missing or malformed the runtime treats it as "no
condition" (always-satisfied) — workflow authors are warned at save
time when their expression fails to compile, so a malformed
condition shouldn't get this far in practice.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import jsonata  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — runtime image always has it
    jsonata = None


def evaluate_success_when(expression: str | None, result: Any) -> bool:
    """Return True if ``expression`` evaluates truthy against ``result``.

    ``expression=None`` or empty string → always True (no condition).
    Compile / runtime errors → True (don't trap the loop forever on a
    bad user expression; log + move on).
    """
    if not expression or not expression.strip():
        return True
    if jsonata is None:
        logger.warning("jsonata not installed — success_when treated as always-true")
        return True
    try:
        compiled = jsonata.Jsonata(expression)
        value = compiled.evaluate(result)
        return bool(value)
    except Exception as exc:
        logger.warning("success_when expression failed (%s); treating as satisfied", exc)
        return True


def expression_is_valid(expression: str | None) -> tuple[bool, str | None]:
    """Static check used by the workflow save endpoint.

    Returns ``(True, None)`` for a valid (or empty) expression,
    ``(False, error_message)`` for one that fails to compile.
    """
    if not expression or not expression.strip():
        return True, None
    if jsonata is None:
        return True, None  # cannot validate without the lib; allow
    try:
        jsonata.Jsonata(expression)
        return True, None
    except Exception as exc:
        return False, str(exc)
