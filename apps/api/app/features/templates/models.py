"""Database-backed Template + TemplatePurchase rows.

The Template table stores every marketplace entry — both official seeded
templates (creator_id NULL, is_official True) and user-published ones
(creator_id set, workspace_id set, is_official False). The static seed
JSON files at `seeds/loops/*.json` still ship as fallback / cold-start
content and are imported into this table by `seeder.py` on first boot.

TemplatePurchase tracks who paid (or "received for free") which template;
the existence of a row is what `Install` button checks to gate premium
content. Stripe wiring lives in a follow-up PR — the slot is preserved
via the nullable `stripe_session_id` column so the data model doesn't
need to change when payments land.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column
from sqlmodel import Field

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field

if TYPE_CHECKING:
    pass


class Template(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # creator_id is nullable so deleting a user doesn't take down their
    # published templates — the row stays, the creator chip just shows
    # "Anonymous". Official templates are seeded with creator_id = NULL.
    creator_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL", index=True
    )
    # workspace_id nullable for the same reason — official templates have
    # no workspace; user-published templates belong to one.
    workspace_id: uuid.UUID | None = Field(
        default=None, foreign_key="workspace.id", ondelete="CASCADE", index=True
    )

    slug: str = Field(max_length=160, unique=True, index=True)
    title: str = Field(max_length=160)
    summary: str = Field(default="", max_length=500)
    description: str = Field(default="")
    category: str = Field(max_length=40, index=True)
    kind: str = Field(default="flow", max_length=20)

    # graph snapshot — same shape as Workflow.graph. JSONB so future
    # queries can index into nodes without a full deserialise.
    graph: dict[str, Any] = Field(
        default_factory=lambda: {"nodes": [], "edges": []},
        sa_column=Column(JSON, nullable=False, default=lambda: {"nodes": [], "edges": []}),
    )
    credentials_required: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )
    tools_required: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False, default=list)
    )

    # bg_variant maps directly to the existing inspo-bg-N CSS classes
    # so the card visual stays unchanged from the static gallery.
    bg_variant: str = Field(default="inspo-bg-1", max_length=20)

    is_published: bool = Field(default=True, index=True)
    is_official: bool = Field(default=False, index=True)
    is_premium: bool = Field(default=False)
    price_cents: int = Field(default=0)
    download_count: int = Field(default=0)
    featured: bool = Field(default=False, index=True)

    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()


class TemplatePurchase(SQLModelBase, table=True):
    __tablename__ = "template_purchase"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID = Field(foreign_key="template.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    price_cents: int = Field(default=0)
    # Nullable until Stripe wiring lands — free installs record a row
    # with no session id so the dashboard can still count "owned by user".
    stripe_session_id: str | None = Field(default=None, max_length=255)
    purchased_at: datetime = created_at_field()
