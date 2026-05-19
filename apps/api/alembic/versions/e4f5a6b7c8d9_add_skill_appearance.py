"""add skill appearance

Revision ID: e4f5a6b7c8d9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "skill",
        sa.Column("icon", sa.String(length=64), nullable=False, server_default="BookOpen"),
    )
    op.add_column(
        "skill",
        sa.Column("color", sa.String(length=32), nullable=False, server_default="#8b5cf6"),
    )
    op.alter_column("skill", "icon", server_default=None)
    op.alter_column("skill", "color", server_default=None)


def downgrade() -> None:
    op.drop_column("skill", "color")
    op.drop_column("skill", "icon")
