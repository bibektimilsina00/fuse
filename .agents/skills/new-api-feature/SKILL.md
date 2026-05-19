---
name: new-api-feature
description: "Scaffold a complete backend API feature following the project's layered architecture — SQLAlchemy model, Pydantic schemas, repository, service, FastAPI router, and router registration. Usage: /new-api-feature"
---

# new-api-feature skill

Ask the user for:
1. **Feature name** — singular noun, PascalCase (e.g. `Tag`, `Comment`, `Webhook`)
2. **What it stores** — fields needed (name, type, nullable, default?)
3. **Owner** — does it belong to a `user_id`? Or another parent model?
4. **CRUD operations needed** — list, get, create, update, delete (which ones?)
5. **URL prefix** — e.g. `/tags`, `/comments`

## Files to create

### 1. Model — `apps/api/app/models/<snake_name>.py`

Follow this exact pattern (from `apps/api/app/models/workflow.py`):

```python
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.app.models.user import User

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base


class <ModelName>(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ... user fields here
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="<snake_plural>")
```

Then add the model to `apps/api/app/models/__init__.py` (import it there so Alembic sees it).

Also add the back-reference to `apps/api/app/models/user.py` if it belongs to a user.

### 2. Schemas — `apps/api/app/schemas/<snake_name>.py`

```python
import uuid
from datetime import datetime
from pydantic import BaseModel


class <ModelName>Base(BaseModel):
    # shared fields

class <ModelName>Create(<ModelName>Base):
    # create-only fields

class <ModelName>Update(BaseModel):
    # all optional fields for PATCH

class <ModelName>Out(<ModelName>Base):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID

    model_config = {"from_attributes": True}
```

### 3. Repository — `apps/api/app/repositories/<snake_name>_repository.py`

Follow `apps/api/app/repositories/workflow_repository.py` exactly:

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.models.<snake_name> import <ModelName>


class <ModelName>Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> <ModelName> | None:
        result = await self.db.execute(
            select(<ModelName>).where(<ModelName>.id == id, <ModelName>.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[<ModelName>]:
        result = await self.db.execute(
            select(<ModelName>).where(<ModelName>.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(self, item: <ModelName>) -> <ModelName>:
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(self, item: <ModelName>, data: dict) -> <ModelName>:
        for key, value in data.items():
            setattr(item, key, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item: <ModelName>) -> None:
        await self.db.delete(item)
        await self.db.commit()
```

### 4. Service — `apps/api/app/services/<snake_name>_service.py`

Follow `apps/api/app/services/workflow_service.py`:

```python
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.models.user import User
from apps.api.app.models.<snake_name> import <ModelName>
from apps.api.app.repositories.<snake_name>_repository import <ModelName>Repository
from apps.api.app.schemas.<snake_name> import <ModelName>Create, <ModelName>Update


class <ModelName>Service:
    def __init__(self, db: AsyncSession):
        self.repository = <ModelName>Repository(db)

    async def list(self, user: User) -> list[<ModelName>]:
        return await self.repository.list_by_user(user.id)

    async def get(self, id: uuid.UUID, user: User) -> <ModelName>:
        item = await self.repository.get_by_id_and_user(id, user.id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="<ModelName> not found")
        return item

    async def create(self, data: <ModelName>Create, user: User) -> <ModelName>:
        item = <ModelName>(user_id=user.id, **data.model_dump())
        return await self.repository.create(item)

    async def update(self, id: uuid.UUID, data: <ModelName>Update, user: User) -> <ModelName>:
        item = await self.get(id, user)
        return await self.repository.update(item, data.model_dump(exclude_unset=True))

    async def delete(self, id: uuid.UUID, user: User) -> None:
        item = await self.get(id, user)
        await self.repository.delete(item)
```

### 5. Router — `apps/api/app/api/v1/<snake_plural>/router.py`

Follow `apps/api/app/api/v1/workflows/router.py`:

```python
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.schemas.<snake_name> import <ModelName>Create, <ModelName>Out, <ModelName>Update
from apps.api.app.services.<snake_name>_service import <ModelName>Service

router = APIRouter()

@router.get("/", response_model=list[<ModelName>Out])
async def list_items(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await <ModelName>Service(db).list(current_user)

# ... remaining CRUD routes
```

Also create `apps/api/app/api/v1/<snake_plural>/__init__.py` (empty).

### 6. Register in main router

Add to `apps/api/app/api/v1/router.py`:
```python
from apps.api.app.api.v1.<snake_plural>.router import router as <snake_name>_router
router.include_router(<snake_name>_router, prefix="/<snake_plural>", tags=["<snake_plural>"])
```

## After creating all files

Run `/db-migrate add_<snake_name>` to generate and apply the Alembic migration.
