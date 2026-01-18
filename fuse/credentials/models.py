"""
Credential database models for secure credential storage.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import JSON, Text


class Credential(SQLModel, table=True):
    """Credential database model for storing encrypted credentials."""
    __tablename__ = "credentials"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    type: str = Field(max_length=100)  # e.g., 'google_sheets', 'slack', 'discord'
    data: Dict = Field(default_factory=dict, sa_type=JSON)  # Encrypted credential data
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    description: Optional[str] = Field(default=None, sa_type=Text)
    last_used_at: Optional[datetime] = None
