"""Pydantic / SQLModel schemas for the template marketplace HTTP surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import SQLModel


class CreatorOut(SQLModel):
    """Public-facing creator card for templates.

    Keep this slim — the marketplace shows it inline on every card; the
    detail page can fetch a richer user profile if we want a bio later.
    """

    id: UUID | None
    full_name: str | None
    email: str | None
    avatar_url: str | None


class TemplateListOut(SQLModel):
    """One row on the marketplace grid. Designed to fit the existing
    `TemplateCard` props (idx + label + title + kind + steps + bg) with
    a creator chip + premium badge layered on top."""

    id: UUID
    slug: str
    title: str
    summary: str
    category: str
    kind: str
    bg_variant: str
    is_official: bool
    is_published: bool
    is_premium: bool
    price_cents: int
    download_count: int
    steps: int
    featured: bool
    creator: CreatorOut | None
    # Exposed in the list payload too so the card can render an actual
    # "what this uses" preview instead of a static striped graphic. Kept
    # short — the card preview only needs the head of the list.
    tools_required: list[str] = []
    # Minimal graph snapshot shipped on the list payload so the card can
    # paint a real workflow mini-preview. Lighter than fetching the full
    # detail per card; just the bits the SVG renderer needs (id, type,
    # position, edges). For convenience we just send the full graph dict
    # — payload size is bounded by the seeded set today and we paginate.
    graph: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class TemplateDetailOut(TemplateListOut):
    """Detail page payload — extends list with the long-form description
    + the credentials list. `graph` + `tools_required` already live on
    the base list payload (the marketplace card preview needs them)."""

    description: str
    credentials_required: list[str]


class TemplateListResponse(SQLModel):
    items: list[TemplateListOut]
    total: int
    limit: int
    offset: int


class TemplateCategorySchema(SQLModel):
    id: str
    label: str
    count: int


class TemplateCategoryListResponse(SQLModel):
    categories: list[TemplateCategorySchema]


class PublishTemplateIn(SQLModel):
    """Body for `POST /templates/publish` — kicks off "publish workflow as
    template" flow from the editor.

    The graph is sourced server-side from the workflow row so the caller
    can't smuggle in a forged snapshot. Same for credentials_required +
    tools_required (derived from the graph).
    """

    workflow_id: UUID
    title: str
    summary: str = ""
    description: str = ""
    category: str
    kind: str = "flow"
    bg_variant: str = "inspo-bg-1"
    is_premium: bool = False
    price_cents: int = 0


class UpdateTemplateIn(SQLModel):
    """Body for `PUT /templates/{id}` — creator-only edit. Graph stays
    immutable from this endpoint; updating the source workflow + re-
    publishing is the right flow for graph changes (avoids accidental
    overwrites of a published template)."""

    title: str | None = None
    summary: str | None = None
    description: str | None = None
    category: str | None = None
    kind: str | None = None
    bg_variant: str | None = None
    is_published: bool | None = None
    is_premium: bool | None = None
    price_cents: int | None = None


class InstallResultOut(SQLModel):
    workflow_id: UUID
    message: str
