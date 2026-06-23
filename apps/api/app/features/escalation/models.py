"""Workspace-scoped escalation config row.

Stored 1:1 with workspace (workspace_id is the PK). Absence of a row
means "silent" — the loop records the failure and exits without paging.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field

from apps.api.app.shared.sqlmodel import (
    SQLModelBase,
    created_at_field,
    updated_at_field,
)


class WorkspaceEscalationConfig(SQLModelBase, table=True):
    __tablename__ = "workspace_escalation_config"

    workspace_id: uuid.UUID = Field(
        foreign_key="workspace.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    enabled: bool = Field(default=True)
    slack_webhook_url: str | None = Field(default=None, max_length=500)
    email_to: str | None = Field(default=None, max_length=320)
    webhook_url: str | None = Field(default=None, max_length=500)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
