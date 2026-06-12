"""Per-item output shape with paired-item tracking.

Workflow expressions like ``$('Earlier Node').body.id`` need to resolve to the
*specific* item in "Earlier Node" that the current item descended from — not
to "the last output" of that node. This is the foundation of n8n's paired-item
system and is the only correct answer for multi-item branches and merges.

This module is the type foundation. It is purely additive:

- :class:`PairedItem` — a back-pointer from one output item to the source item
  it was derived from.
- :class:`NodeItem` — one row of a node's output: a dict payload plus an
  optional :class:`PairedItem`.

Wiring (the runner producing these for every node, fan-out nodes setting their
own item lists, the resolver walking the chain) lands in later PRs. Today
nothing produces or consumes these yet.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PairedItem(BaseModel):
    """Provenance link from an output item back to its source input item.

    ``source_node_id`` is the upstream node that produced the input row this
    output row was derived from. ``source_item_index`` is the index of that
    row within the upstream node's output list. Together they form one edge
    of the provenance chain a resolver walks when evaluating cross-node
    expressions inside a multi-item run.
    """

    source_node_id: str
    source_item_index: int = 0


class NodeItem(BaseModel):
    """A single row produced by a node.

    ``data`` mirrors the dict shape today's :attr:`NodeResult.output_data`
    holds. Fan-out nodes (foreach, split, etc.) emit multiple ``NodeItem``s,
    each with its own :class:`PairedItem` pointing back at the input row that
    fanned out.
    """

    data: dict[str, Any] = Field(default_factory=dict)
    paired_item: PairedItem | None = None
