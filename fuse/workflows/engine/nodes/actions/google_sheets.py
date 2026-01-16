"""Google Sheets integration nodes"""
from typing import Any, Dict
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry


@NodeRegistry.register
class GoogleSheetsReadNode(BaseNode):
    """Google Sheets read operation"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="google_sheets.read",
            label="Google Sheets Read",
            type="action",
            description="Reads rows from a Google Sheet.",
            category="Data",
            inputs=[
                NodeInput(name="auth", type="credential", label="Google Account", credential_type="google_sheets", required=True),
                NodeInput(
                    name="spreadsheet_id", 
                    type="select", 
                    label="Spreadsheet", 
                    required=True,
                    dynamic_options="list_spreadsheets",
                    dynamic_dependencies=["auth"]
                ),
                NodeInput(name="range", type="string", label="Range (A1)")
            ],
            outputs=[
                NodeOutput(name="rows", type="array", label="Rows")
            ]
        )
    
    async def list_spreadsheets(self, context: Dict[str, Any], dependency_values: Dict[str, Any]) -> list[Dict[str, str]]:
        """Fetch list of Google Sheets from Drive."""
        cred_id = dependency_values.get("auth")
        if not cred_id:
            return []
            
        from fuse.credentials.service import get_active_credential
        import httpx
        
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
                pass
                
        return options

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # Check for auth
        config = context.get("node_config", {})
        cred_id = config.get("auth")
        if not cred_id:
             raise ValueError("Google Account credential is required for Google Sheets operations")
        
        from fuse.credentials.service import get_active_credential
        import httpx
        
        cred = await get_active_credential(cred_id)
        if not cred or not cred.get("data", {}).get("access_token"):
            raise ValueError(f"Invalid or missing credential: {cred_id}")
            
        token = cred["data"]["access_token"]
        spreadsheet_id = config.get("spreadsheet_id")
        range_name = config.get("range", "A1:Z100")
        
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}"
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise RuntimeError(f"Google Sheets API returned {response.status_code}: {response.text}")
                
            data = response.json()
            return {"rows": data.get("values", [])}


@NodeRegistry.register
class GoogleSheetsWriteNode(BaseNode):
    """Google Sheets write operation"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="google_sheets.write",
            label="Google Sheets Write",
            type="action",
            description="Appends rows to a Google Sheet.",
            category="Data",
            inputs=[
                NodeInput(name="auth", type="credential", label="Google Account", credential_type="google_sheets", required=True),
                # Dynamic Spreadsheet Selection
                NodeInput(
                    name="spreadsheet_id", 
                    type="select", 
                    label="Spreadsheet", 
                    required=True,
                    dynamic_options="list_spreadsheets",
                    dynamic_dependencies=["auth"]
                ),
                NodeInput(
                    name="new_sheet_name",
                    type="string",
                    label="New Spreadsheet Name",
                    required=False,
                    description="Required if 'Create New Spreadsheet' is selected above.",
                    show_if={"spreadsheet_id": "NEW"}
                ),
                NodeInput(name="range", type="string", label="Range (e.g. Sheet1!A1)", default="Sheet1!A1"),
                NodeInput(name="data", type="json", label="Row Data (Array of Arrays)")
            ],
            outputs=[
                NodeOutput(name="success", type="boolean", label="Success"),
                NodeOutput(name="updates", type="json", label="Update Details")
            ]
        )
    
    async def list_spreadsheets(self, context: Dict[str, Any], dependency_values: Dict[str, Any]) -> list[Dict[str, str]]:
        """Fetch list of Google Sheets from Drive."""
        cred_id = dependency_values.get("auth")
        if not cred_id:
            return []
            
        from fuse.credentials.service import get_active_credential
        import httpx
        
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
                        # Only show files we can edit to avoid 403s on write
                        if f.get("capabilities", {}).get("canEdit"):
                            owner = f.get('owners', [{}])[0].get('displayName', 'Unknown')
                            desc = f"Owner: {owner} • Modified: {f.get('modifiedTime', '')[:10]}"
                            options.append({"label": f["name"], "value": f["id"], "description": desc})
            except Exception as e:
                # Log error or return empty
                pass
                
        return options

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        # Check for auth
        config = context.get("node_config", {})
        cred_id = config.get("auth")
        if not cred_id:
             raise ValueError("Google Account credential is required for Google Sheets operations")

        from fuse.credentials.service import get_active_credential
        import httpx
        
        cred = await get_active_credential(cred_id)
        if not cred or not cred.get("data", {}).get("access_token"):
             raise ValueError(f"Invalid or missing credential: {cred_id}")

        token = cred["data"]["access_token"]
        spreadsheet_id = config.get("spreadsheet_id")
        
        # Handle "Create New" logic
        if spreadsheet_id == "NEW":
            new_name = config.get("new_sheet_name")
            if not new_name:
                # Fallback name
                new_name = f"Automation Sheet {context.get('execution_id', '')[:8]}"
            
            # Create the sheet
            create_url = "https://sheets.googleapis.com/v4/spreadsheets"
            create_body = {
                "properties": {"title": new_name}
            }
            create_headers = {"Authorization": f"Bearer {token}"}
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(create_url, headers=create_headers, json=create_body)
                if resp.status_code != 200:
                    raise RuntimeError(f"Failed to create new spreadsheet: {resp.text}")
                
                new_sheet_data = resp.json()
                spreadsheet_id = new_sheet_data.get("spreadsheetId")
                # Update config in context for future reference if needed? 
                # (Can't update persistent config here easily without DB write, but subsequent steps won't know)
                # However, for this node execution, it works.

        if not spreadsheet_id:
             raise ValueError("Spreadsheet ID is required")

        range_name = config.get("range", "Sheet1!A1")
        row_data = config.get("data")
        
        if not row_data:
            # Try to use input_data if config data is empty? 
            # Often users pass data from previous node
            if isinstance(input_data, list):
                row_data = input_data
            elif isinstance(input_data, dict):
                row_data = [list(input_data.values())]
            else:
                row_data = [[str(input_data)]]
        
        # Jinja2 Templating Logic for row_data
        from jinja2 import Template
        
        # Construct template context
        template_context = {
            "input": input_data,
            "workflow_id": context.get("workflow_id"),
            "execution_id": context.get("execution_id"),
            **context.get("results", {}),
            **(input_data if isinstance(input_data, dict) else {})
        }

        def recursive_render(item):
            if isinstance(item, str) and "{{" in item and "}}" in item:
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
        
        # Ensure it's a list of lists
        if not isinstance(row_data, list):
            # If it's a single value (string, dict, etc), wrap it as a single cell in a single row
            row_data = [[row_data]]
        elif len(row_data) > 0 and not isinstance(row_data[0], list):
             # If it's a flat list [1, 2], wrap it as a single row [[1, 2]]
             row_data = [row_data]

        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}:append"
        params = {"valueInputOption": "USER_ENTERED"}
        headers = {"Authorization": f"Bearer {token}"}
        body = {"values": row_data}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body, params=params)
             
            if response.status_code != 200:
                if response.status_code == 403:
                     raise RuntimeError(f"Permission denied. You may not have edit access to this spreadsheet (ID: {spreadsheet_id}). Please check sharing settings or try creating a new sheet.")
                elif response.status_code == 404:
                     raise RuntimeError(f"Spreadsheet not found (ID: {spreadsheet_id}). It may have been deleted or the ID is incorrect.")
                
                # Parse JSON error for cleaner message if possible
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
                    
                raise RuntimeError(f"Google Sheets API Error ({response.status_code}): {error_text}")
            
            return {
                "success": True,
                "updates": response.json(),
                "spreadsheet_id": spreadsheet_id # Return ID used
            }
