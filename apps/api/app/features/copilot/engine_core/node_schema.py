"""Node-schema discovery & compression for the Copilot.

Two-tier strategy so node context scales to hundreds/1000+ node types without
prompt bloat — and without a curated allow-list that drifts as nodes are added:

  • Tier 1 (in the system prompt): a *complete* index of every registered
    workflow node, split by category. Triggers and logic nodes get the full
    `type **Name** — description` line because they shape control flow. Action
    nodes get a compact `type **Name**` roster — name alone is enough for the
    model to know they exist and decide to fetch metadata. `build_node_index`.
  • Tier 2 (on demand, via tools): `get_node_metadata([...])` returns
    `project_node` — a compressed projection (NOT the raw NodeMetadata) with
    fields, operations, outputs, etc. `search_node_types` covers fuzzy queries
    (e.g. "crm" → hubspot/salesforce).

`project_node` is the single shared projection consumed by the metadata tool
and the validator, so they never drift. The prompt index is derived purely
from registered metadata — adding a new node automatically surfaces it; no
curated `CORE_NODE_TYPES` to maintain.
"""

from __future__ import annotations

from typing import Any

# Map the rich UI property types down to a few JSON types the model reasons about.
_SIMPLE_TYPE_MAP: dict[str, str] = {
    "string": "string",
    "long-string": "string",
    "code": "string",
    "number": "number",
    "boolean": "boolean",
    "json": "json",
    "schema": "json",
    "options": "string",
    "multi-options": "array",
    "key-value": "object",
    "list": "array",
    "file-list": "array",
    "messages": "array",
    "tool-selector": "array",
    "skill-selector": "array",
    "credential": "credential",
}

_WORKFLOW_NODE_PREFIXES = ("trigger.", "action.", "logic.")
# Triggers and logic (control flow) come first because they shape the workflow;
# everything else (action / ai / integration / …) follows in registry order.
_CATEGORY_ORDER = ["trigger", "logic"]


def is_workflow_node(meta: dict[str, Any]) -> bool:
    """True for placeable workflow nodes (excludes credential-provider definitions)."""
    return str(meta.get("type", "")).startswith(_WORKFLOW_NODE_PREFIXES)


def _simple_type(prop_type: str) -> str:
    return _SIMPLE_TYPE_MAP.get(prop_type, "string")


def _is_hidden(prop: dict[str, Any]) -> bool:
    return prop.get("visibility") == "hidden"


def _is_required(prop: dict[str, Any]) -> bool:
    # Conditional-required ({field, value}) is treated as optional in the projection;
    # the validator enforces required-when-visible against live values.
    return prop.get("required") is True


def _enum_values(prop: dict[str, Any]) -> list[Any] | None:
    opts = prop.get("options")
    if not isinstance(opts, list):
        return None
    values: list[Any] = []
    for opt in opts:
        if isinstance(opt, dict):
            values.append(opt.get("value", opt.get("label")))
        else:
            values.append(opt)
    cleaned = [v for v in values if v is not None]
    return cleaned or None


def _condition_operations(prop: dict[str, Any]) -> list[Any] | None:
    """If a prop is gated on the `operation` field, return the operation value(s)
    it applies to. Handles leaf `{field, value}` and composite `{all|any:[...]}`."""
    cond = prop.get("condition")
    if not isinstance(cond, dict):
        return None
    if cond.get("field") == "operation":
        val = cond.get("value")
        return list(val) if isinstance(val, list) else [val]
    ops: list[Any] = []
    for key in ("all", "any"):
        subs = cond.get(key)
        if isinstance(subs, list):
            for sub in subs:
                if isinstance(sub, dict) and sub.get("field") == "operation":
                    val = sub.get("value")
                    ops.extend(val if isinstance(val, list) else [val])
    return ops or None


def _field_summary(prop: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "name": prop.get("name"),
        "type": _simple_type(str(prop.get("type", "string"))),
    }
    if prop.get("description"):
        summary["description"] = prop["description"]
    enum = _enum_values(prop)
    if enum is not None:
        summary["options"] = enum
    if prop.get("loadOptions"):
        # Dynamic options are fetched at runtime (network/credential-dependent) — do
        # not enumerate. Tell the model it's a free value resolved later.
        summary["dynamic"] = True
        summary["note"] = (
            "options are fetched at runtime; pass a concrete id/value or leave for the user"
        )
    if prop.get("default") is not None:
        summary["default"] = prop["default"]
    return summary


def project_node(meta: dict[str, Any]) -> dict[str, Any]:
    """Compress a raw NodeMetadata dict into the compact, LLM-optimized schema.

    Splits fields into required/optional, buckets operation-gated fields under
    `operations`, resolves static enums, marks dynamic options, strips hidden
    fields, and attaches outputs + credential requirement.
    """
    props = [p for p in meta.get("properties", []) if not _is_hidden(p)]

    common_required: list[dict[str, Any]] = []
    common_optional: list[dict[str, Any]] = []
    operations: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for prop in props:
        summary = _field_summary(prop)
        bucket = "required" if _is_required(prop) else "optional"
        ops = _condition_operations(prop)
        if ops:
            for op in ops:
                op_key = str(op)
                operations.setdefault(op_key, {"required": [], "optional": []})
                operations[op_key][bucket].append(summary)
        else:
            (common_required if bucket == "required" else common_optional).append(summary)

    outputs = [
        {"name": o.get("label"), "type": o.get("type", "any")}
        for o in meta.get("outputs_schema", [])
        if isinstance(o, dict)
    ]

    schema: dict[str, Any] = {
        "type": meta.get("type"),
        "name": meta.get("name"),
        "category": meta.get("category"),
        "description": meta.get("description"),
        "inputs": {"required": common_required, "optional": common_optional},
    }
    if operations:
        schema["operations"] = operations
    if outputs:
        schema["outputs"] = outputs
    if meta.get("credential_type"):
        schema["credential"] = meta["credential_type"]
    if meta.get("allow_error"):
        schema["supports_error_output"] = True
    return schema


# ── Tier-1 index + discovery helpers ──────────────────────────────────────────

# Categories that get the full `type **Name** — description` line in the index
# because they shape workflow control flow and the model needs to reason about
# *which* one to pick before calling get_node_metadata. Everything else (i.e.
# the long tail of integrations and actions) gets the compact roster format,
# which scales linearly with the registry size without prompt bloat.
_FULL_LINE_CATEGORIES: frozenset[str] = frozenset({"trigger", "logic"})


def _full_line(meta: dict[str, Any]) -> str:
    return f"- `{meta.get('type', '')}` **{meta.get('name', '')}** — {meta.get('description', '')}"


def _roster_line(meta: dict[str, Any]) -> str:
    return f"- `{meta.get('type', '')}` **{meta.get('name', '')}**"


def build_node_index(node_metadata: list[dict[str, Any]]) -> str:
    """Complete prompt index of every registered workflow node, grouped by
    category. Triggers + logic get full descriptions; actions get the compact
    roster (name only). Derived purely from metadata — no curated allow-list.
    """
    by_category: dict[str, list[str]] = {}
    for meta in node_metadata:
        if not is_workflow_node(meta):
            continue
        category = meta.get("category", "other")
        line = _full_line(meta) if category in _FULL_LINE_CATEGORIES else _roster_line(meta)
        by_category.setdefault(category, []).append(line)

    categories = _CATEGORY_ORDER + [c for c in by_category if c not in _CATEGORY_ORDER]
    sections: list[str] = []
    for category in categories:
        lines = by_category.get(category)
        if not lines:
            continue
        heading = (
            f"### {category} (full details below — pick by description)"
            if category in _FULL_LINE_CATEGORIES
            else f"### {category} (roster — call `get_node_metadata` for fields)"
        )
        sections.append(f"{heading}\n" + "\n".join(sorted(lines)))
    return "\n\n".join(sections)


def list_trigger_node_types(node_metadata: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "type": m.get("type", ""),
            "name": m.get("name", ""),
            "description": m.get("description", ""),
        }
        for m in node_metadata
        if m.get("category") == "trigger"
    ]


def search_node_types(
    node_metadata: list[dict[str, Any]],
    query: str,
    limit: int = 15,
) -> list[dict[str, str]]:
    """Keyword/substring search over type/name/description/category for long-tail
    discovery. Same interface a future embedding/RAG implementation would keep."""
    q = query.lower().strip()
    if not q:
        return []
    hits: list[dict[str, str]] = []
    for meta in node_metadata:
        if not is_workflow_node(meta):
            continue
        haystack = " ".join(
            str(meta.get(k, "")) for k in ("type", "name", "description", "category")
        ).lower()
        if q in haystack:
            hits.append(
                {
                    "type": meta.get("type", ""),
                    "name": meta.get("name", ""),
                    "description": meta.get("description", ""),
                }
            )
        if len(hits) >= limit:
            break
    return hits
