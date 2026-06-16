"""Google Sheets action node — full CRUD over a user's spreadsheets via
OAuth. One node, twelve operations.

Read & write
  - `get_spreadsheet`  / `get_values`
  - `update_values`    / `append_values`
  - `clear_values`

Create
  - `create_spreadsheet` (title + initial sheets[])
  - `create_sheet`       (add a tab to an existing spreadsheet)
  - `duplicate_sheet`    (copy a tab in-place)

Modify
  - `find_replace`       (string search + replace, optionally scoped to one sheet)
  - `batch_update`       (raw `requests[]` for power users)

Delete
  - `delete_sheet`       (remove a tab from a spreadsheet)
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"


class GoogleSheetsProperties(BaseModel):
    credential: str | None = None
    operation: str = "get_values"

    spreadsheet_id: str | None = None
    range_name: str | None = None

    # update / append
    value_input_option: str = "USER_ENTERED"
    values: Any = None  # list[list[Any]] when literal; Any allows templates

    # create_spreadsheet
    title: str | None = None
    initial_sheets: Any = None  # list[str] of sheet titles for the new spreadsheet

    # create_sheet / duplicate_sheet / delete_sheet
    sheet_title: str | None = None
    source_sheet_id: int | None = None
    sheet_id_num: int | None = None

    # find_replace
    find: str | None = None
    replace: str | None = None
    sheet_name: str | None = None  # optional scope
    match_case: bool = False
    match_entire_cell: bool = False

    # batch_update — raw API requests array
    requests: Any = None

    @field_validator("spreadsheet_id", mode="before")
    @classmethod
    def _coerce_spreadsheet_id(cls, value: Any) -> str | None:
        # The picker emits `{id, name}` so the editor can show the picked
        # spreadsheet's name back — runtime only cares about the id.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)

    @field_validator("source_sheet_id", "sheet_id_num", mode="before")
    @classmethod
    def _coerce_sheet_numeric_id(cls, value: Any) -> int | None:
        # Tab picker may emit `{sheet_id, title}` — collapse to the numeric id.
        if isinstance(value, dict):
            v = value.get("sheet_id")
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @field_validator("sheet_name", mode="before")
    @classmethod
    def _coerce_sheet_name(cls, value: Any) -> str | None:
        # Tab picker (`valueAs="title"`) emits a plain string title;
        # accept dict form too for forward-compat.
        if isinstance(value, dict):
            v = value.get("title")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleSheetsNode(BaseNode[GoogleSheetsProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleSheetsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.google_sheets",
            name="Google Sheets",
            category="integration",
            description=(
                "Read, write, create, and modify Google Sheets via OAuth — "
                "values, sheets, find/replace, and raw batch requests."
            ),
            icon="si:SiGooglesheets",
            color="#0f9d58",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "get_values",
                    "options": [
                        {"label": "Read Values", "value": "get_values"},
                        {"label": "Update Values", "value": "update_values"},
                        {"label": "Append Values", "value": "append_values"},
                        {"label": "Clear Values", "value": "clear_values"},
                        {"label": "Get Spreadsheet Metadata", "value": "get_spreadsheet"},
                        {"label": "Create Spreadsheet", "value": "create_spreadsheet"},
                        {"label": "Add Sheet (Tab)", "value": "create_sheet"},
                        {"label": "Duplicate Sheet", "value": "duplicate_sheet"},
                        {"label": "Delete Sheet", "value": "delete_sheet"},
                        {"label": "Find & Replace", "value": "find_replace"},
                        {"label": "Batch Update (Raw)", "value": "batch_update"},
                    ],
                },
                # spreadsheet_id — required for everything except create_spreadsheet
                {
                    "name": "spreadsheet_id",
                    "label": "Spreadsheet",
                    "type": "gsheet-spreadsheet",
                    "required": True,
                    "condition": _cond_any(
                        "get_spreadsheet",
                        "get_values",
                        "update_values",
                        "append_values",
                        "clear_values",
                        "create_sheet",
                        "duplicate_sheet",
                        "delete_sheet",
                        "find_replace",
                        "batch_update",
                    ),
                },
                # range_name — used by value-based ops
                {
                    "name": "range_name",
                    "label": "Range",
                    "type": "string",
                    "placeholder": "Sheet1!A1:D10",
                    "required": True,
                    "condition": _cond_any(
                        "get_values", "update_values", "append_values", "clear_values"
                    ),
                },
                # update / append shared options
                {
                    "name": "value_input_option",
                    "label": "Value parsing",
                    "type": "options",
                    "default": "USER_ENTERED",
                    "options": [
                        {"label": "User Entered (parses formulas, dates)", "value": "USER_ENTERED"},
                        {"label": "Raw (no parsing)", "value": "RAW"},
                    ],
                    "condition": _cond_any("update_values", "append_values"),
                    "mode": "advanced",
                },
                {
                    "name": "values",
                    "label": "Values",
                    "type": "json",
                    "placeholder": '[["Header1", "Header2"], ["Val1", "Val2"]]',
                    "description": "Array of rows. Each row is an array of cell values.",
                    "required": True,
                    "condition": _cond_any("update_values", "append_values"),
                },
                # create_spreadsheet
                {
                    "name": "title",
                    "label": "Spreadsheet title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Q1 Reports",
                    "condition": _cond("create_spreadsheet"),
                },
                {
                    "name": "initial_sheets",
                    "label": "Initial sheets",
                    "type": "json",
                    "placeholder": '["Summary", "Details"]',
                    "description": "Optional array of sheet titles. Defaults to one sheet named Sheet1.",
                    "condition": _cond("create_spreadsheet"),
                    "mode": "advanced",
                },
                # create_sheet
                {
                    "name": "sheet_title",
                    "label": "Sheet title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Q2",
                    "condition": _cond_any("create_sheet", "duplicate_sheet"),
                },
                # duplicate_sheet / delete_sheet — picker emits the numeric sheetId
                {
                    "name": "source_sheet_id",
                    "label": "Source sheet",
                    "type": "gsheet-tab",
                    "required": True,
                    "typeOptions": {"valueAs": "sheet_id"},
                    "condition": _cond("duplicate_sheet"),
                },
                {
                    "name": "sheet_id_num",
                    "label": "Sheet to delete",
                    "type": "gsheet-tab",
                    "required": True,
                    "typeOptions": {"valueAs": "sheet_id"},
                    "condition": _cond("delete_sheet"),
                },
                # find_replace
                {
                    "name": "find",
                    "label": "Find",
                    "type": "string",
                    "required": True,
                    "placeholder": "old text",
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "replace",
                    "label": "Replace with",
                    "type": "string",
                    "placeholder": "new text",
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "sheet_name",
                    "label": "Scope to sheet",
                    "type": "gsheet-tab",
                    "typeOptions": {"valueAs": "title"},
                    "description": "Leave blank to search every sheet.",
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                {
                    "name": "match_case",
                    "label": "Match case",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                {
                    "name": "match_entire_cell",
                    "label": "Match entire cell",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                # batch_update
                {
                    "name": "requests",
                    "label": "Requests (raw)",
                    "type": "json",
                    "required": True,
                    "placeholder": '[{"updateSheetProperties": {"properties": {"sheetId": 0, "title": "Renamed"}, "fields": "title"}}]',
                    "description": "Raw Sheets API `requests[]` array. See Sheets API docs.",
                    "condition": _cond("batch_update"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "spreadsheetId", "type": "string"},
                {"label": "values", "type": "array"},
                {"label": "updatedRange", "type": "string"},
                {"label": "updatedRows", "type": "number"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Sheets API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleSheetsNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── operation handlers ──────────────────────────────────────────────────


def _require_spreadsheet_id(node: GoogleSheetsNode) -> str | NodeResult:
    sid = (node.props.spreadsheet_id or "").strip()
    if not sid:
        return NodeResult(success=False, error="Spreadsheet ID required.")
    return sid


def _require_range(node: GoogleSheetsNode) -> str | NodeResult:
    rng = (node.props.range_name or "").strip()
    if not rng:
        return NodeResult(success=False, error="Range is required.")
    return rng


async def _get_spreadsheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    r = await client.get(f"{SHEETS_API}/{sid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    r = await client.get(f"{SHEETS_API}/{sid}/values/{rng}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _update_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    body = {
        "range": rng,
        "majorDimension": "ROWS",
        "values": node.props.values or [],
    }
    r = await client.put(
        f"{SHEETS_API}/{sid}/values/{rng}",
        headers=headers,
        json=body,
        params={"valueInputOption": node.props.value_input_option},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _append_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    body = {
        "range": rng,
        "majorDimension": "ROWS",
        "values": node.props.values or [],
    }
    r = await client.post(
        f"{SHEETS_API}/{sid}/values/{rng}:append",
        headers=headers,
        json=body,
        params={
            "valueInputOption": node.props.value_input_option,
            "insertDataOption": "INSERT_ROWS",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _clear_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    r = await client.post(f"{SHEETS_API}/{sid}/values/{rng}:clear", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _create_spreadsheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="Title is required.")
    body: dict[str, Any] = {"properties": {"title": title}}
    raw_sheets = node.props.initial_sheets
    sheet_titles: list[str] = []
    if isinstance(raw_sheets, list):
        sheet_titles = [str(t) for t in raw_sheets if str(t).strip()]
    if sheet_titles:
        body["sheets"] = [{"properties": {"title": t}} for t in sheet_titles]
    r = await client.post(SHEETS_API, headers=headers, json=body)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _batch_update_request(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    sid: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    r = await client.post(
        f"{SHEETS_API}/{sid}:batchUpdate",
        headers=headers,
        json={"requests": requests},
    )
    r.raise_for_status()
    return r.json()


async def _create_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    title = (node.props.sheet_title or "").strip()
    if not title:
        return NodeResult(success=False, error="Sheet title is required.")
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [{"addSheet": {"properties": {"title": title}}}],
    )
    return NodeResult(success=True, output_data=result)


async def _duplicate_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    if node.props.source_sheet_id is None:
        return NodeResult(success=False, error="Source sheet ID is required.")
    title = (node.props.sheet_title or "").strip()
    req: dict[str, Any] = {"duplicateSheet": {"sourceSheetId": int(node.props.source_sheet_id)}}
    if title:
        req["duplicateSheet"]["newSheetName"] = title
    result = await _batch_update_request(client, headers, sid, [req])
    return NodeResult(success=True, output_data=result)


async def _delete_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    if node.props.sheet_id_num is None:
        return NodeResult(success=False, error="Sheet ID is required.")
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [{"deleteSheet": {"sheetId": int(node.props.sheet_id_num)}}],
    )
    return NodeResult(success=True, output_data=result)


async def _find_replace(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    find = node.props.find or ""
    if find == "":
        return NodeResult(success=False, error="Find value is required.")
    body: dict[str, Any] = {
        "find": find,
        "replacement": node.props.replace or "",
        "matchCase": bool(node.props.match_case),
        "matchEntireCell": bool(node.props.match_entire_cell),
    }
    sheet_name = (node.props.sheet_name or "").strip()
    if sheet_name:
        # Resolve sheet name → numeric sheetId so we can target it precisely.
        # `find_replace` accepts either a `range` or a `sheetId`; pick sheetId
        # because the user gave us a name, not a range.
        meta = await client.get(
            f"{SHEETS_API}/{sid}",
            headers=headers,
            params={"fields": "sheets.properties(sheetId,title)"},
        )
        meta.raise_for_status()
        sheet_id_num: int | None = None
        for sh in meta.json().get("sheets") or []:
            props = (sh or {}).get("properties") or {}
            if str(props.get("title") or "") == sheet_name:
                sheet_id_num = int(props.get("sheetId"))
                break
        if sheet_id_num is None:
            return NodeResult(
                success=False, error=f"Sheet '{sheet_name}' not found in spreadsheet."
            )
        body["sheetId"] = sheet_id_num
    else:
        body["allSheets"] = True
    result = await _batch_update_request(client, headers, sid, [{"findReplace": body}])
    return NodeResult(success=True, output_data=result)


async def _batch_update(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    requests = node.props.requests
    if not isinstance(requests, list) or not requests:
        return NodeResult(
            success=False,
            error="`requests` must be a non-empty array of Sheets API request objects.",
        )
    result = await _batch_update_request(client, headers, sid, requests)
    return NodeResult(success=True, output_data=result)


_HANDLERS: dict[str, Any] = {
    "get_spreadsheet": _get_spreadsheet,
    "get_values": _get_values,
    "update_values": _update_values,
    "append_values": _append_values,
    "clear_values": _clear_values,
    "create_spreadsheet": _create_spreadsheet,
    "create_sheet": _create_sheet,
    "duplicate_sheet": _duplicate_sheet,
    "delete_sheet": _delete_sheet,
    "find_replace": _find_replace,
    "batch_update": _batch_update,
}
