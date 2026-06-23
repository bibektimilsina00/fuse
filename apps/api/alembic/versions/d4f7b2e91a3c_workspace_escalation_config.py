"""workspace_escalation_config table

Revision ID: d4f7b2e91a3c
Revises: a1c5e9b2f0d8
Create Date: 2026-06-23 12:00:00.000000

Per-workspace 1:1 row holding the escalation channel config used by
``failure_policy=escalate`` agent loops. Schema matches
``apps/api/app/features/escalation/models.py`` exactly — keep them in
sync when columns change.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from apps.api.app.shared.sqlmodel import UTCDateTime

# revision identifiers, used by Alembic.
revision = "d4f7b2e91a3c"
down_revision = "a1c5e9b2f0d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_escalation_config",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspace.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("slack_webhook_url", sa.String(length=500), nullable=True),
        sa.Column("email_to", sa.String(length=320), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
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
    )


def downgrade() -> None:
    op.drop_table("workspace_escalation_config")
