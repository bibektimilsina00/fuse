import uuid
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from fuse.auth.schemas import UserBase

if TYPE_CHECKING:
    from fuse.workflows.models import Workflow


class User(UserBase, table=True):
    """User database model"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    workflows: list["Workflow"] = Relationship(back_populates="owner")
