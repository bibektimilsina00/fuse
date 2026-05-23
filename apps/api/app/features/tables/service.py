import csv
import io
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.tables.models import DataTable, TableColumn, TableRow
from apps.api.app.features.tables.repository import TableRepository
from apps.api.app.features.tables.schemas import (
    TableColumnCreate,
    TableColumnOut,
    TableCreate,
    TableImportOut,
    TableImportRowsOut,
    TableRowOut,
    TableRowsOut,
    TableRowUpsert,
    TableSummaryOut,
)
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace


class TableService:
    """Service layer executing business logic for Tables."""

    def __init__(self, db: AsyncSession):
        self.repository = TableRepository(db)

    def _summary_out(
        self, table: DataTable, row_count: int, column_count: int, owner: User
    ) -> TableSummaryOut:
        """Helper to construct a TableSummaryOut schema."""
        return TableSummaryOut(
            id=table.id,
            name=table.name,
            description=table.description,
            row_count=row_count,
            column_count=column_count,
            source=table.description or "Manual table",
            owner=owner.full_name or owner.email,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )

    async def _get_table(self, table_id: uuid.UUID, workspace_id: uuid.UUID) -> DataTable:
        """Helper to get a table or raise 404."""
        t = await self.repository.get_table_by_id(table_id, workspace_id)
        if not t:
            raise HTTPException(status_code=404, detail="Table not found")
        return t

    async def list_tables(self, current_user: User, workspace: Workspace) -> list[TableSummaryOut]:
        """List tables in the workspace."""
        results = await self.repository.list_tables_summary(workspace.id)
        return [
            self._summary_out(t, int(row_count or 0), int(column_count or 0), current_user)
            for t, row_count, column_count in results
        ]

    async def create_table(
        self, body: TableCreate, current_user: User, workspace: Workspace
    ) -> TableSummaryOut:
        """Create a new table with a default column 'name'."""
        table = DataTable(
            workspace_id=workspace.id,
            user_id=current_user.id,
            name=body.name.strip(),
            description=body.description,
        )
        col = TableColumn(name="name", col_type="text", position=0)
        created = await self.repository.create_table(table, col)
        return self._summary_out(created, 0, 1, current_user)

    async def import_csv_as_table(
        self, filename: str, content: str, current_user: User, workspace: Workspace
    ) -> TableImportOut:
        """Create a table and populate it with rows from a CSV."""
        table_name = filename.rsplit(".", 1)[0].strip() or "Imported table"
        table = DataTable(
            workspace_id=workspace.id,
            user_id=current_user.id,
            name=table_name[:200],
            description="CSV import",
        )
        await self.repository.add(table)
        await self.repository.flush()

        reader = csv.DictReader(io.StringIO(content))
        headers = [header for header in (reader.fieldnames or []) if header]

        col_map: dict[str, str] = {}
        for position, header in enumerate(headers):
            col = TableColumn(
                table_id=table.id, name=header[:200], col_type="text", position=position
            )
            await self.repository.add(col)
            await self.repository.flush()
            col_map[header] = str(col.id)

        row_count = 0
        for position, row in enumerate(reader):
            data = {col_map[key]: value for key, value in row.items() if key in col_map}
            await self.repository.add(TableRow(table_id=table.id, position=position, data=data))
            row_count += 1

        await self.repository.commit()
        await self.repository.refresh(table)
        return TableImportOut(
            **self._summary_out(table, row_count, len(headers), current_user).model_dump()
        )

    async def delete_table(self, table_id: uuid.UUID, workspace: Workspace) -> None:
        """Delete a table."""
        t = await self._get_table(table_id, workspace.id)
        await self.repository.delete_table(t)

    async def add_column(
        self, table_id: uuid.UUID, body: TableColumnCreate, workspace: Workspace
    ) -> TableColumnOut:
        """Add a column to a table."""
        await self._get_table(table_id, workspace.id)
        pos = await self.repository.get_column_count(table_id)
        col = TableColumn(
            table_id=table_id,
            name=body.name.strip(),
            col_type=body.col_type,
            position=pos,
            options=body.options,
        )
        await self.repository.add(col)
        await self.repository.commit()
        await self.repository.refresh(col)
        return TableColumnOut(
            id=col.id,
            name=col.name,
            col_type=col.col_type,
            position=col.position,
            options=col.options,
        )

    async def update_column(
        self,
        table_id: uuid.UUID,
        column_id: uuid.UUID,
        body: TableColumnCreate,
        workspace: Workspace,
    ) -> TableColumnOut:
        """Update a column's name, type, and options."""
        await self._get_table(table_id, workspace.id)
        col = await self.repository.get_column(column_id, table_id)
        if not col:
            raise HTTPException(404, "Column not found")
        col.name = body.name.strip()
        col.col_type = body.col_type
        col.options = body.options
        await self.repository.commit()
        return TableColumnOut(
            id=col.id,
            name=col.name,
            col_type=col.col_type,
            position=col.position,
            options=col.options,
        )

    async def delete_column(
        self, table_id: uuid.UUID, column_id: uuid.UUID, workspace: Workspace
    ) -> None:
        """Delete a column from a table."""
        await self._get_table(table_id, workspace.id)
        col = await self.repository.get_column(column_id, table_id)
        if not col:
            raise HTTPException(404, "Column not found")
        await self.repository.db.delete(col)
        await self.repository.commit()

    async def list_rows(self, table_id: uuid.UUID, workspace: Workspace) -> TableRowsOut:
        """List columns and rows for a table."""
        t = await self._get_table(table_id, workspace.id)
        rows = await self.repository.list_rows(table_id)
        cols = [
            TableColumnOut(
                id=c.id,
                name=c.name,
                col_type=c.col_type,
                position=c.position,
                options=c.options,
            )
            for c in t.columns
        ]
        return TableRowsOut(
            columns=cols,
            rows=[TableRowOut(id=row.id, data=row.data, position=row.position) for row in rows],
        )

    async def add_row(
        self, table_id: uuid.UUID, body: TableRowUpsert | None, workspace: Workspace
    ) -> TableRowOut:
        """Add a row to a table."""
        await self._get_table(table_id, workspace.id)
        pos = await self.repository.get_row_count(table_id)
        row = TableRow(table_id=table_id, position=pos, data=body.data if body else {})
        await self.repository.add(row)
        await self.repository.commit()
        await self.repository.refresh(row)
        return TableRowOut(id=row.id, data=row.data, position=row.position)

    async def update_row(
        self, table_id: uuid.UUID, row_id: uuid.UUID, body: TableRowUpsert, workspace: Workspace
    ) -> TableRowOut:
        """Update a row's data fields."""
        await self._get_table(table_id, workspace.id)
        row = await self.repository.get_row(row_id, table_id)
        if not row:
            raise HTTPException(404, "Row not found")
        row.data = {**row.data, **body.data}
        await self.repository.commit()
        return TableRowOut(id=row.id, data=row.data, position=row.position)

    async def delete_row(
        self, table_id: uuid.UUID, row_id: uuid.UUID, workspace: Workspace
    ) -> None:
        """Delete a row from a table."""
        await self._get_table(table_id, workspace.id)
        row = await self.repository.get_row(row_id, table_id)
        if not row:
            raise HTTPException(404, "Row not found")
        await self.repository.db.delete(row)
        await self.repository.commit()

    async def export_csv(self, table_id: uuid.UUID, workspace: Workspace) -> tuple[str, str]:
        """Export table columns and rows as a CSV string."""
        t = await self._get_table(table_id, workspace.id)
        rows = await self.repository.list_rows(table_id)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([c.name for c in t.columns])
        for row in rows:
            writer.writerow([row.data.get(str(c.id), "") for c in t.columns])
        return buf.getvalue(), t.name

    async def import_csv(
        self, table_id: uuid.UUID, content: str, workspace: Workspace
    ) -> TableImportRowsOut:
        """Import rows from a CSV, creating any new columns found in the CSV header."""
        t = await self._get_table(table_id, workspace.id)
        reader = csv.DictReader(io.StringIO(content))
        col_map = {c.name: str(c.id) for c in t.columns}

        for header in reader.fieldnames or []:
            if header not in col_map:
                pos = await self.repository.get_column_count(table_id)
                col = TableColumn(table_id=table_id, name=header, col_type="text", position=pos)
                await self.repository.add(col)
                await self.repository.flush()
                col_map[header] = str(col.id)

        pos = await self.repository.get_row_count(table_id)
        imported = 0
        for row in reader:
            data = {col_map[k]: v for k, v in row.items() if k in col_map}
            await self.repository.add(TableRow(table_id=t.id, position=pos, data=data))
            pos += 1
            imported += 1
        await self.repository.commit()
        return TableImportRowsOut(imported=imported)


def get_table_service(db: AsyncSession = Depends(get_db)) -> TableService:
    """Dependency helper for TableService."""
    return TableService(db)
