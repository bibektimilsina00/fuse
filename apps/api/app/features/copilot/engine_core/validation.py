"""Per-field validation + graph lint for the Copilot.

Validates the LLM's `inputs` against each node type's real property schema and
returns structured, named errors so the model self-corrects. Condition/visibility
semantics mirror the frontend `shouldShowProperty` (leaf `{field,value}` and
composite `{all|any:[...]}`) so prompt, canvas, and validation never disagree.
"""

from __future__ import annotations

import json
from typing import Any

# ── Condition / visibility (mirrors frontend shouldShowProperty) ───────────────


def matches_condition(condition: Any, values: dict[str, Any]) -> bool:
    if not isinstance(condition, dict):
        return True
    if "all" in condition:
        return all(matches_condition(c, values) for c in (condition.get("all") or []))
    if "any" in condition:
        return any(matches_condition(c, values) for c in (condition.get("any") or []))
    field = condition.get("field")
    if not field:
        return True
    current = values.get(field)
    expected = condition.get("value")
    if isinstance(expected, list):
        return current in expected
    return current == expected


def is_visible(prop: dict[str, Any], values: dict[str, Any]) -> bool:
    cond = prop.get("condition")
    return True if cond is None else matches_condition(cond, values)


def is_required(prop: dict[str, Any], values: dict[str, Any]) -> bool:
    req = prop.get("required")
    if req is True:
        return True
    if isinstance(req, dict):  # conditional-required {field, value}
        return matches_condition(req, values)
    return False


# ── Per-field coercion / validation ───────────────────────────────────────────


def _option_values(prop: dict[str, Any]) -> list[Any] | None:
    opts = prop.get("options")
    if not isinstance(opts, list):
        return None
    values = [o.get("value", o.get("label")) if isinstance(o, dict) else o for o in opts]
    cleaned = [v for v in values if v is not None]
    return cleaned or None


def _coerce(prop: dict[str, Any], value: Any) -> tuple[bool, Any, str | None]:
    """Return (ok, coerced_value, error_message)."""
    ptype = str(prop.get("type", "string"))
    if value is None:
        return True, value, None

    if ptype == "number":
        if isinstance(value, bool):
            return False, value, "expected a number"
        if isinstance(value, int | float):
            return True, value, None
        if isinstance(value, str) and value.strip():
            try:
                return True, float(value) if "." in value else int(value), None
            except ValueError:
                return False, value, f"expected a number, got {value!r}"
        return False, value, "expected a number"

    if ptype == "boolean":
        if isinstance(value, bool):
            return True, value, None
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return True, value.lower() == "true", None
        return False, value, "expected a boolean"

    if ptype == "options":
        allowed = _option_values(prop)
        if allowed is not None and value not in allowed:
            return False, value, f"must be one of {allowed}"
        return True, value, None

    if ptype == "multi-options":
        if not isinstance(value, list):
            return False, value, "expected an array"
        allowed = _option_values(prop)
        if allowed is not None:
            bad = [v for v in value if v not in allowed]
            if bad:
                return False, value, f"invalid options {bad}; allowed {allowed}"
        return True, value, None

    if ptype in ("json", "schema", "key-value"):
        if isinstance(value, dict | list):
            return True, value, None
        if isinstance(value, str):
            try:
                return True, json.loads(value), None
            except json.JSONDecodeError:
                return True, value, None  # may be an interpolation expression
        return True, value, None

    # lenient string-ish / array types
    return True, value, None


def validate_node_inputs(
    node_type: str,
    props_values: Any,
    meta: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate & coerce *provided* inputs against the node schema.

    Drops unknown fields and fields not visible given the other values; coerces
    typed values; collects structured errors. Does NOT enforce required-missing
    (that is `check_required`, run on the final node state).
    """
    if not isinstance(props_values, dict):
        return {}, [
            {
                "node_type": node_type,
                "field": "(root)",
                "value": props_values,
                "error": "properties must be an object",
            }
        ]

    schema_props = {p.get("name"): p for p in meta.get("properties", []) if p.get("name")}
    clean: dict[str, Any] = {}
    errors: list[dict[str, Any]] = []

    for name, value in props_values.items():
        prop = schema_props.get(name)
        if prop is None:
            errors.append(
                {
                    "node_type": node_type,
                    "field": name,
                    "value": value,
                    "error": "unknown field for this node type",
                }
            )
            continue
        if not is_visible(prop, props_values):
            continue  # not applicable given the other values — drop quietly
        ok, coerced, err = _coerce(prop, value)
        if not ok:
            errors.append({"node_type": node_type, "field": name, "value": value, "error": err})
            continue
        clean[name] = coerced

    return clean, errors


def check_required(
    node_type: str,
    final_props: dict[str, Any],
    meta: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flag required fields that are visible given `final_props` but missing/empty.
    Run against the final node state (after merging edits), not partial op inputs."""
    errors: list[dict[str, Any]] = []
    for prop in meta.get("properties", []):
        name = prop.get("name")
        if not name:
            continue
        if (
            is_required(prop, final_props)
            and is_visible(prop, final_props)
            and final_props.get(name) in (None, "")
        ):
            errors.append(
                {
                    "node_type": node_type,
                    "field": name,
                    "value": None,
                    "error": "missing required field",
                }
            )
    return errors


# ── Graph lint ─────────────────────────────────────────────────────────────────


def lint_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Lightweight structural lint. Returns only non-empty findings."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = {n.get("id") for n in nodes}
    targets = {e.get("target") for e in edges}

    orphan_nodes = [
        n.get("id")
        for n in nodes
        if not str(n.get("type", "")).startswith("trigger.") and n.get("id") not in targets
    ]
    dangling_edges = [
        e.get("id") or f"{e.get('source')}->{e.get('target')}"
        for e in edges
        if e.get("source") not in node_ids or e.get("target") not in node_ids
    ]

    result: dict[str, Any] = {}
    if orphan_nodes:
        result["orphan_nodes"] = orphan_nodes
    if dangling_edges:
        result["dangling_edges"] = dangling_edges
    return result
