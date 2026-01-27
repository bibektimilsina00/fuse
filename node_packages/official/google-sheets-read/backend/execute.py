"""
Google Sheets Read Node Plugin

Read data from Google Sheets.
"""

import httpx
import logging
from typing import Any, Dict, List

from fuse.credentials.service import get_active_credential

logger = logging.getLogger(__name__)


async def list_spreadsheets(context: Dict[str, Any], dependency_values: Dict[str, Any]) -> List[Dict[str, str]]:
    """Fetch list of Google Sheets from Drive."""
    cred_id = dependency_values.get("auth")
    if not cred_id:
        return []
        
    cred = await get_active_credential(cred_id)
    if not cred or not cred.get("data", {}).get("access_token"):
        return []
        
    token = cred["data"]["access_token"]
    options = []
    
    url = "https://www.googleapis.com/drive/v3/files"
    params = {
        "q": "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
        "pageSize": 50,
        "fields": "files(id, name, modifiedTime, owners(displayName))"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                files = resp.json().get("files", [])
                for f in files:
                    owner = f.get('owners', [{}])[0].get('displayName', 'Unknown')
                    desc = f"Owner: {owner} • Modified: {f.get('modifiedTime', '')[:10]}"
                    options.append({"label": f["name"], "value": f["id"], "description": desc})
        except Exception as e:
            logger.warning(f"Failed to list spreadsheets: {e}")
            
    return options


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """Read rows from Google Sheet."""
    config = context.get("config", {})
    
    # 1. Authenticate
    cred_id = config.get("auth")
    if not cred_id:
         raise ValueError("Google Account credential is required")

    cred = await get_active_credential(cred_id)
    if not cred or not cred.get("data", {}).get("access_token"):
         raise ValueError(f"Invalid or missing credential: {cred_id}")

    token = cred["data"]["access_token"]
    spreadsheet_id = config.get("spreadsheet_id")
    if not spreadsheet_id:
         raise ValueError("Spreadsheet ID is required")

    range_name = config.get("range", "Sheet1!A1:Z50")
    
    # 2. Execute Read
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
             raise RuntimeError(f"Google Sheets API Error ({response.status_code}): {response.text}")
            
        data = response.json()
        return {"rows": data.get("values", [])}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    errors = []
    if not config.get("auth"):
        errors.append("Google Account is required")
    if not config.get("spreadsheet_id"):
        errors.append("Spreadsheet is required")
    return {"valid": len(errors) == 0, "errors": errors}
