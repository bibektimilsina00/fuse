"""
Google Sheets Write Node Plugin

Append data to Google Sheets.
"""

import httpx
import logging
from jinja2 import Template
from typing import Any, Dict, List, Optional

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


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append rows to Google Sheet.
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    
    # 1. Authenticate
    cred_id = config.get("auth")
    if not cred_id:
         raise ValueError("Google Account credential is required")

    cred = await get_active_credential(cred_id)
    if not cred or not cred.get("data", {}).get("access_token"):
         raise ValueError(f"Invalid or missing credential: {cred_id}")

    token = cred["data"]["access_token"]
    spreadsheet_id = config.get("spreadsheet_id")
    
    # 2. Handle "Create New Spreadsheet"
    if spreadsheet_id == "NEW":
        new_name = config.get("new_sheet_name")
        if not new_name:
            new_name = f"Automation Output {context.get('execution_id', '')[:8]}"
        
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
    range_name = config.get("range", "Sheet1!A1")
    row_data = config.get("data")
    
    if not row_data:
        # Fallback to direct input if config is empty
        if isinstance(inputs, list):
            row_data = inputs
        elif isinstance(inputs, dict):
            row_data = [list(inputs.values())]
        else:
            row_data = [[str(inputs)]]
    
    # 4. Render Templates
    template_context = {
        "input": inputs,
        "inputs": inputs,
        "workflow_id": context.get("workflow_id"),
        "execution_id": context.get("execution_id"),
        **context.get("results", {}),
        **(inputs if isinstance(inputs, dict) else {})
    }

    def recursive_render(item):
        if isinstance(item, str) and "{{" in item:
            try:
                return Template(item).render(template_context)
            except Exception:
                return item
        elif isinstance(item, list):
            return [recursive_render(i) for i in item]
        elif isinstance(item, dict):
            return {k: recursive_render(v) for k, v in item.items()}
        return item

    if row_data:
        row_data = recursive_render(row_data)
    
    # Normalize to list of lists
    if not isinstance(row_data, list):
        row_data = [[row_data]]
    elif len(row_data) > 0 and not isinstance(row_data[0], list):
         row_data = [row_data]

    # 5. Execute Append
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append"
    params = {"valueInputOption": "USER_ENTERED"}
    headers = {"Authorization": f"Bearer {token}"}
    body = {"values": row_data}
    
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
        
        return {
            "success": True,
            "updates": response.json(),
            "spreadsheet_id": spreadsheet_id
        }


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("auth"):
        errors.append("Google Account is required")
    if not config.get("spreadsheet_id"):
        errors.append("Spreadsheet is required")
    return {"valid": len(errors) == 0, "errors": errors}
