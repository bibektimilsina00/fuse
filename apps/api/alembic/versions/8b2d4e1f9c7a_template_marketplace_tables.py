"""template marketplace tables

Revision ID: 8b2d4e1f9c7a
Revises: 31e103ee3b6d
Create Date: 2026-06-23 16:00:00.000000

Adds the `template` table for the marketplace + `template_purchase`
companion table that gates premium content (Stripe wiring lands in a
follow-up; the slot is preserved here). Both tables cascade on
workspace/user delete so removing an account doesn't leave orphans.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from apps.api.app.shared.sqlmodel import UTCDateTime

revision = "8b2d4e1f9c7a"
down_revision = "31e103ee3b6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "creator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False, server_default="flow"),
        sa.Column("graph", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "credentials_required",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "tools_required",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column("bg_variant", sa.String(length=20), nullable=False, server_default="inspo-bg-1"),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("slug", name="uq_template_slug"),
    )
    op.create_index("ix_template_creator_id", "template", ["creator_id"])
    op.create_index("ix_template_workspace_id", "template", ["workspace_id"])
    op.create_index("ix_template_category", "template", ["category"])
    op.create_index("ix_template_is_published", "template", ["is_published"])
    op.create_index("ix_template_is_official", "template", ["is_official"])
    op.create_index("ix_template_featured", "template", ["featured"])

    op.create_table(
        "template_purchase",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("template.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stripe_session_id", sa.String(length=255), nullable=True),
        sa.Column(
            "purchased_at",
            UTCDateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_template_purchase_template_id", "template_purchase", ["template_id"])
    op.create_index("ix_template_purchase_user_id", "template_purchase", ["user_id"])
    op.create_index("ix_template_purchase_workspace_id", "template_purchase", ["workspace_id"])


def downgrade() -> None:
    op.drop_table("template_purchase")
    op.drop_table("template")
