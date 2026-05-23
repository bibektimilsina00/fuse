import uuid
from collections.abc import Sequence

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.folders.models import Folder
from apps.api.app.features.folders.repository import FolderRepository
from apps.api.app.features.folders.schemas import FolderCreate, FolderUpdate


class FolderService:
    """Service layer executing business logic for Folders."""

    def __init__(self, db: AsyncSession):
        self.repository = FolderRepository(db)

    async def create_folder(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, schema: FolderCreate
    ) -> Folder:
        """Create a new folder in a workspace."""
        folder = Folder(
            user_id=user_id,
            workspace_id=workspace_id,
            name=schema.name,
            parent_id=schema.parent_id,
        )
        return await self.repository.create(folder)

    async def get_folders(self, workspace_id: uuid.UUID) -> Sequence[Folder]:
        """Get all folders in a workspace."""
        return await self.repository.list_by_workspace(workspace_id)

    async def get_folder(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> Folder | None:
        """Get a specific folder in a workspace."""
        return await self.repository.get_by_id_and_workspace(folder_id, workspace_id)

    async def update_folder(
        self, workspace_id: uuid.UUID, folder_id: uuid.UUID, schema: FolderUpdate
    ) -> Folder | None:
        """Update properties of a folder."""
        folder = await self.get_folder(workspace_id, folder_id)
        if not folder:
            return None

        update_dict = {}
        if schema.name is not None:
            update_dict["name"] = schema.name
        if schema.parent_id is not None:
            update_dict["parent_id"] = schema.parent_id

        return await self.repository.update(folder, update_dict)

    async def delete_folder(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> bool:
        """Delete a folder and all its associated workflows."""
        folder = await self.get_folder(workspace_id, folder_id)
        if not folder:
            return False

        # Delete workflows within the folder first
        await self.repository.delete_workflows_by_folder(folder_id, workspace_id)
        # Delete folder itself
        await self.repository.delete(folder)
        return True


def get_folder_service(db: AsyncSession = Depends(get_db)) -> FolderService:
    """Dependency helper for FolderService."""
    return FolderService(db)
