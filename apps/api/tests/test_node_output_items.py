"""Tests for the per-item NodeResult shape (PR2 — types only).

These tests pin the type behaviour. Wiring into the runner and individual
nodes happens in PR3 onward.
"""

from __future__ import annotations

from apps.api.app.node_system.base.node_item import NodeItem, PairedItem
from apps.api.app.node_system.base.node_result import NodeResult


def test_get_items_default_wraps_output_data() -> None:
    result = NodeResult(success=True, output_data={"key": "value"})
    items = result.get_items()
    assert len(items) == 1
    assert items[0].data == {"key": "value"}
    assert items[0].paired_item is None


def test_get_items_default_empty_output_data() -> None:
    result = NodeResult(success=True)
    items = result.get_items()
    assert items == [NodeItem(data={})]


def test_get_items_returns_explicit_items_verbatim() -> None:
    explicit = [
        NodeItem(data={"row": 0}),
        NodeItem(data={"row": 1}),
        NodeItem(data={"row": 2}),
    ]
    result = NodeResult(success=True, items=explicit)
    items = result.get_items()
    # `items` survives Pydantic validation as an equivalent list (it may not
    # be the same object — Pydantic rebuilds validated children — but the
    # values must match exactly, in order).
    assert items == explicit


def test_paired_item_attaches_and_serialises() -> None:
    item = NodeItem(
        data={"id": 42},
        paired_item=PairedItem(source_node_id="http_request-1", source_item_index=3),
    )
    result = NodeResult(success=True, items=[item])

    # Round-trip through Pydantic to confirm the field survives serialisation —
    # workflow event emission and DB persistence both rely on this.
    payload = result.model_dump()
    rebuilt = NodeResult.model_validate(payload)

    assert rebuilt.items is not None
    assert len(rebuilt.items) == 1
    assert rebuilt.items[0].data == {"id": 42}
    paired = rebuilt.items[0].paired_item
    assert paired is not None
    assert paired.source_node_id == "http_request-1"
    assert paired.source_item_index == 3


def test_legacy_node_result_construction_unchanged() -> None:
    # Constructors that existed before this PR (no `items` kwarg) must still
    # produce a valid NodeResult. This is the backwards-compatibility guarantee.
    result = NodeResult(
        success=False,
        output_data={"error_code": "TIMEOUT"},
        error="Upstream timed out",
        logs=["attempt 1 failed", "attempt 2 failed"],
        handled_successors=False,
    )
    assert result.items is None
    assert result.get_items() == [NodeItem(data={"error_code": "TIMEOUT"})]


def test_explicit_items_and_output_data_coexist() -> None:
    # Some fan-out nodes will both populate `output_data` (legacy summary,
    # e.g. {"count": 3, "results": [...]}) AND the per-row `items` list. The
    # `items` list wins for paired-item lookups; `output_data` stays available
    # for legacy `{{nodeId.output.count}}` interpolation until PR10's cutover.
    result = NodeResult(
        success=True,
        output_data={"count": 2, "results": [{"x": 1}, {"x": 2}]},
        items=[NodeItem(data={"x": 1}), NodeItem(data={"x": 2})],
    )
    items = result.get_items()
    assert len(items) == 2
    assert [i.data for i in items] == [{"x": 1}, {"x": 2}]
    # Legacy field untouched.
    assert result.output_data["count"] == 2


def test_paired_item_index_defaults_to_zero() -> None:
    paired = PairedItem(source_node_id="upstream-id")
    assert paired.source_item_index == 0
