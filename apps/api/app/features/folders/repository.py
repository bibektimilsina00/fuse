import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.folders.models import Folder
from apps.api.app.features.workflows.models import Workflow


class FolderRepository:
    """Repository for handling database operations on Folder models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_workspace(
        self, folder_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Folder | None:
        """Retrieve a folder by ID within a workspace."""
        stmt = select(Folder).where(Folder.id == folder_id, Folder.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> Sequence[Folder]:
        """List folders in a workspace."""
        stmt = select(Folder).where(Folder.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, folder: Folder) -> Folder:
        """Create a new folder."""
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def update(self, folder: Folder, data: dict) -> Folder:
        """Update fields of an existing folder."""
        for key, value in data.items():
            setattr(folder, key, value)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def delete_workflows_by_folder(
        self, folder_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        """Delete all workflows in a folder."""
        await self.db.execute(
            delete(Workflow).where(
                Workflow.folder_id == folder_id, Workflow.workspace_id == workspace_id
            )
        )

    async def delete(self, folder: Folder) -> None:
        """Delete a folder."""
        await self.db.delete(folder)
        await self.db.commit()
