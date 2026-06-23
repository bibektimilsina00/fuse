"""merge phase5 cron drift + workspace escalation config

Revision ID: 31e103ee3b6d
Revises: c8e3f7a45b1d, d4f7b2e91a3c
Create Date: 2026-06-23 16:35:42.660539

"""

from collections.abc import Sequence

revision: str = "31e103ee3b6d"
down_revision: str | None = ("c8e3f7a45b1d", "d4f7b2e91a3c")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
