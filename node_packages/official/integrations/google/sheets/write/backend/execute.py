"""
Google Sheets Write Node Plugin

Append data to Google Sheets.
"""

from typing import Any, Dict, List, Optional
import logging
import httpx
from jinja2 import Template
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

from fuse.credentials.service import get_active_credential

logger = logging.getLogger(__name__)

async def list_spreadsheets(context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Fetch list of Google Sheets from Drive.
    """
    cred_id = dependency_values.get("auth")
    if not cred_id:
        return []
        
    cred = await get_active_credential(cred_id)
    if not cred or not cred.get("data", {}).get("access_token"):
        return []
        
    token = cred["data"]["access_token"]
    options = []
    
    # Add "Create New" option first
    options.append({"label": "[+] Create New Spreadsheet", "value": "NEW"})
    
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        "pageSize": 50,
        "fields": "files(id, name, modifiedTime, owners(displayName), capabilities(canEdit))"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                files = resp.json().get("files", [])
                for f in files:
                    # Only show files we can edit
                    if f.get("capabilities", {}).get("canEdit"):
                        owner = f.get('owners', [{}])[0].get('displayName', 'Unknown')
                        desc = f"Owner: {owner} • Modified: {f.get('modifiedTime', '')[:10]}"
                        options.append({"label": f["name"], "value": f["id"], "description": desc})
        except Exception as e:
            logger.warning(f"Failed to list spreadsheets: {e}")
            
    return options


async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Append rows to Google Sheet.
    """
    # Use resolve_config() for basic fields, but for 'data' doing manual per-item resolution is better
    # to support batch processing
    resolved_config = context.resolve_config()
    raw_config = context.raw_config
    
    items = context.input_data # List[WorkflowItem]
    
    # 1. Authenticate
    cred_id = resolved_config.get("auth")
    if not cred_id:
         raise ValueError("Google Account credential is required")

    cred = await get_active_credential(cred_id)
    if not cred or not cred.get("data", {}).get("access_token"):
         raise ValueError(f"Invalid or missing credential: {cred_id}")

    token = cred["data"]["access_token"]
    spreadsheet_id = resolved_config.get("spreadsheet_id")
    
    # 2. Handle "Create New Spreadsheet"
    if spreadsheet_id == "NEW":
        new_name = resolved_config.get("new_sheet_name")
        if not new_name:
            new_name = f"Automation Output {context.execution_id[:8]}"
        
        create_url = "https://sheets.googleapis.com/v4/spreadsheets"
        create_body = {"properties": {"title": new_name}}
        create_headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(create_url, headers=create_headers, json=create_body)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to create new spreadsheet: {resp.text}")
            
            new_sheet_data = resp.json()
            spreadsheet_id = new_sheet_data.get("spreadsheetId")

    if not spreadsheet_id:
         raise ValueError("Spreadsheet ID is required")

    # 3. Prepare Data
    range_name = resolved_config.get("range", "Sheet1!A1")
    
    rows_to_append = []
    
    # Logic:
    # If raw 'data' is provided, we treat it as a template to run for EACH item.
    # If not provided, we try to dump item values.
    
    row_template_raw = raw_config.get("data")
    
    def render_row(template, item_ctx):
         if isinstance(template, str) and "{{" in template:
              try:
                  return Template(template).render(item_ctx)
              except:
                  return template
         elif isinstance(template, list):
              return [render_row(i, item_ctx) for i in template]
         return template

    if row_template_raw:
        # If input has items, iterate them. If empty, iterate once with empty context.
        # But wait, usually 'input_data' is a list.
        loop_items = items if items else [WorkflowItem(json={})]
        
        for item in loop_items:
             item_ctx = {
                 "input": item.json_data, 
                 "inputs": item.json_data,
                 "workflow_id": context.workflow_id,
                 "execution_id": context.execution_id
             }
             
             rendered_rows = render_row(row_template_raw, item_ctx)
             
             # Expand if the template result is a list of lists 
             # (e.g. template was [["{{input.a}}", "{{input.b}}"]])
             if isinstance(rendered_rows, list):
                 if len(rendered_rows) > 0 and isinstance(rendered_rows[0], list):
                      rows_to_append.extend(rendered_rows)
                 else:
                      rows_to_append.append(rendered_rows)
             else:
                  # Weird case where template resolved to single value?
                  rows_to_append.append([rendered_rows])
                  
    else:
        # Fallback: Dump values from items unsorted
        if items:
             for item in items:
                 if isinstance(item.json_data, dict):
                     rows_to_append.append(list(item.json_data.values()))
                 else:
                     rows_to_append.append([str(item.json_data)])
        else:
             # Just dump what's in resolved inputs if any?
             # Probably nothing to write if no items and no config.
             pass

    if not rows_to_append:
        # Nothing to write
        return []

    # 5. Execute Append
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append"
    params = {"valueInputOption": "USER_ENTERED"}
    headers = {"Authorization": f"Bearer {token}"}
    body = {"values": rows_to_append}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=body, params=params)
            
        if response.status_code != 200:
            error_text = response.text
            try:
                err_json = response.json()
                if "error" in err_json:
                    if isinstance(err_json["error"], dict) and "message" in err_json["error"]:
                            error_text = f"{err_json['error']['message']} (Status: {err_json['error'].get('status')})"
                    elif "message" in err_json:
                            error_text = err_json["message"]
            except:
                pass
                
            if response.status_code == 403:
                raise RuntimeError(f"Permission denied for sheet {spreadsheet_id}")
            elif response.status_code == 404:
                raise RuntimeError(f"Spreadsheet not found: {spreadsheet_id}")
            
            raise RuntimeError(f"Google Sheets API Error ({response.status_code}): {error_text}")
        
        # Output info about the operation
        # We return 1 item with success metadata.
        # We could pass through the original items, but since we aggregated specific rows, 
        # checking "success" is usually what matters for a Write node.
        # Or we can return all items "passed through".
        # Standard Write node: Return incoming items? Or Return success stats?
        # I'll return success stats for now as it matches V1 behavior.
        
        return [WorkflowItem(
            json={
                "success": True,
                "updates": response.json(),
                "spreadsheet_id": spreadsheet_id,
                "rows_appended": len(rows_to_append)
            }
        )]


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("auth"):
        errors.append("Google Account is required")
    if not config.get("spreadsheet_id"):
        errors.append("Spreadsheet is required")
    return {"valid": len(errors) == 0, "errors": errors}
