from __future__ import annotations

import csv
import io
import uuid
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.models.table import DataTable, TableColumn, TableRow
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace

router = APIRouter()


class TableCreate(BaseModel):
    name: str
    description: str | None = None


class ColumnCreate(BaseModel):
    name: str
    col_type: str = "text"
    options: dict | None = None


class RowUpsert(BaseModel):
    data: dict[str, Any]


async def _get_table(table_id: uuid.UUID, workspace_id: uuid.UUID, db: AsyncSession) -> DataTable:
    result = await db.execute(
        sa.select(DataTable)
        .where(DataTable.id == table_id, DataTable.workspace_id == workspace_id)
        .options(selectinload(DataTable.columns))
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Table not found")
    return t


# ── Tables CRUD ───────────────────────────────────────────────────────────────


@router.get("/")
async def list_tables(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(DataTable).where(DataTable.workspace_id == workspace.id).order_by(DataTable.name)
    )
    tables = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in tables
    ]


@router.post("/", status_code=201)
async def create_table(
    body: TableCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    table = DataTable(
        workspace_id=workspace.id,
        user_id=current_user.id,
        name=body.name.strip(),
        description=body.description,
    )
    db.add(table)
    await db.flush()
    # Add default "name" column
    col = TableColumn(table_id=table.id, name="name", col_type="text", position=0)
    db.add(col)
    await db.commit()
    await db.refresh(table)
    return {"id": str(table.id), "name": table.name}


@router.delete("/{table_id}", status_code=204)
async def delete_table(
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    t = await _get_table(table_id, workspace.id, db)
    await db.delete(t)
    await db.commit()


# ── Columns ───────────────────────────────────────────────────────────────────


@router.post("/{table_id}/columns", status_code=201)
async def add_column(
    table_id: uuid.UUID,
    body: ColumnCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    count_r = await db.execute(
        sa.select(sa.func.count(TableColumn.id)).where(TableColumn.table_id == table_id)
    )
    pos = count_r.scalar() or 0
    col = TableColumn(
        table_id=table_id,
        name=body.name.strip(),
        col_type=body.col_type,
        position=pos,
        options=body.options,
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return {"id": str(col.id), "name": col.name, "col_type": col.col_type, "position": col.position}


@router.patch("/{table_id}/columns/{column_id}")
async def update_column(
    table_id: uuid.UUID,
    column_id: uuid.UUID,
    body: ColumnCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableColumn).where(TableColumn.id == column_id, TableColumn.table_id == table_id)
    )
    col = r.scalar_one_or_none()
    if not col:
        raise HTTPException(404, "Column not found")
    col.name = body.name.strip()
    col.col_type = body.col_type
    col.options = body.options
    await db.commit()
    return {"id": str(col.id), "name": col.name, "col_type": col.col_type, "position": col.position}


@router.delete("/{table_id}/columns/{column_id}", status_code=204)
async def delete_column(
    table_id: uuid.UUID,
    column_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableColumn).where(TableColumn.id == column_id, TableColumn.table_id == table_id)
    )
    col = r.scalar_one_or_none()
    if not col:
        raise HTTPException(404, "Column not found")
    await db.delete(col)
    await db.commit()


# ── Rows ──────────────────────────────────────────────────────────────────────


@router.get("/{table_id}/rows")
async def list_rows(
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    t = await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableRow)
        .where(TableRow.table_id == table_id)
        .order_by(TableRow.position, TableRow.created_at)
    )
    rows = r.scalars().all()
    cols = [
        {"id": str(c.id), "name": c.name, "col_type": c.col_type, "position": c.position}
        for c in t.columns
    ]
    return {
        "columns": cols,
        "rows": [{"id": str(row.id), "data": row.data, "position": row.position} for row in rows],
    }


@router.post("/{table_id}/rows", status_code=201)
async def add_row(
    table_id: uuid.UUID,
    body: RowUpsert | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    count_r = await db.execute(
        sa.select(sa.func.count(TableRow.id)).where(TableRow.table_id == table_id)
    )
    pos = count_r.scalar() or 0
    row = TableRow(table_id=table_id, position=pos, data=body.data if body else {})
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "data": row.data, "position": row.position}


@router.patch("/{table_id}/rows/{row_id}")
async def update_row(
    table_id: uuid.UUID,
    row_id: uuid.UUID,
    body: RowUpsert,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableRow).where(TableRow.id == row_id, TableRow.table_id == table_id)
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Row not found")
    row.data = {**row.data, **body.data}
    await db.commit()
    return {"id": str(row.id), "data": row.data}


@router.delete("/{table_id}/rows/{row_id}", status_code=204)
async def delete_row(
    table_id: uuid.UUID,
    row_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableRow).where(TableRow.id == row_id, TableRow.table_id == table_id)
    )
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Row not found")
    await db.delete(row)
    await db.commit()


# ── CSV Import / Export ───────────────────────────────────────────────────────


@router.get("/{table_id}/export.csv")
async def export_csv(
    table_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    t = await _get_table(table_id, workspace.id, db)
    r = await db.execute(
        sa.select(TableRow).where(TableRow.table_id == table_id).order_by(TableRow.position)
    )
    rows = r.scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([c.name for c in t.columns])
    for row in rows:
        writer.writerow([row.data.get(str(c.id), "") for c in t.columns])
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{t.name}.csv"'},
    )


@router.post("/{table_id}/import.csv", status_code=201)
async def import_csv(
    table_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    t = await _get_table(table_id, workspace.id, db)
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    col_map = {c.name: str(c.id) for c in t.columns}
    # Auto-create missing columns
    for header in reader.fieldnames or []:
        if header not in col_map:
            count_r = await db.execute(
                sa.select(sa.func.count(TableColumn.id)).where(TableColumn.table_id == table_id)
            )
            pos = count_r.scalar() or 0
            col = TableColumn(table_id=table_id, name=header, col_type="text", position=pos)
            db.add(col)
            await db.flush()
            col_map[header] = str(col.id)
    count_r = await db.execute(
        sa.select(sa.func.count(TableRow.id)).where(TableRow.table_id == table_id)
    )
    pos = count_r.scalar() or 0
    for row in reader:
        data = {col_map[k]: v for k, v in row.items() if k in col_map}
        db.add(TableRow(table_id=table_id, position=pos, data=data))
        pos += 1
    await db.commit()
    return {"imported": pos}
