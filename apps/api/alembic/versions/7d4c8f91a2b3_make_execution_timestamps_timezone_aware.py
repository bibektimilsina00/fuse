"""make execution timestamps timezone aware

Revision ID: 7d4c8f91a2b3
Revises: 5fad5564b104
Create Date: 2026-05-16 23:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7d4c8f91a2b3"
down_revision: str | None = "5fad5564b104"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "execution",
        "started_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="started_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "execution",
        "finished_at",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="finished_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "executionlog",
        "timestamp",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="timestamp AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "executionlog",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        postgresql_using="timestamp AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "execution",
        "finished_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="finished_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "execution",
        "started_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="started_at AT TIME ZONE 'UTC'",
    )
