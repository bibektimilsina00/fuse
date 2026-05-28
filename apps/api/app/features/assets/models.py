from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field


class Asset(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=255)
    file_path: str = Field(max_length=1000)
    file_type: str = Field(max_length=255)
    file_size: int = Field()
    source_type: str = Field(default="uploaded", max_length=50)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()
