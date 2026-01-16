
import httpx
from typing import Any, Dict
from src.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from src.workflows.engine.nodes.registry import NodeRegistry
from src.workflows.utils.templating import render_values

@NodeRegistry.register
class HTTPRequestNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="http.request",
            label="HTTP Request",
            type="action",
            description="Makes an external API request.",
            category="Utilities",
            inputs=[
                NodeInput(name="url", type="string", label="URL", required=True),
                NodeInput(name="method", type="select", label="Method", default="GET", options=[
                    {"label": "GET", "value": "GET"},
                    {"label": "POST", "value": "POST"}
                ]),
                NodeInput(name="body", type="json", label="JSON Body", default="{}", required=False)
            ],
            outputs=[
                NodeOutput(name="data", type="json", label="Response Data"),
                NodeOutput(name="status", type="number", label="Status Code")
            ],
            runtime="http",
            error_policy="retry"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        
        # Prepare context for templating
        # We allow access to input_data primarily
        tpl_context = {
            "input_data": input_data,
            "context": context
        }

        # Resolve values locally for now
        # Strategy: 
        # 1. Get raw value from config
        # 2. If missing, look in input_data (legacy support) but this is brittle
        # 3. Render the value using templating
        
        raw_url = config.get("url")
        raw_method = config.get("method") or "GET"
        raw_headers = config.get("headers") or {}
        raw_body = config.get("body") or {}

        # Legacy fallback logic (if config is empty, try to get from input)
        # We only apply this if config is explicitly empty
        if not raw_url and isinstance(input_data, dict) and "url" in input_data:
             raw_url = input_data["url"]
        
        if not raw_url:
             pass # Will fail check below
             
        # Render everything
        url = render_values(raw_url, tpl_context)
        
        # Rule: Ensure protocol is present
        if url and not url.startswith(("http://", "https://")):
            url = f"https://{url}"
            
        method = render_values(raw_method, tpl_context)
        headers = render_values(raw_headers, tpl_context)
        body = render_values(raw_body, tpl_context)

        if not url:
            raise ValueError("URL is required for HTTP Request node")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, headers=headers, json=body)
                try:
                    # Attempt to parse json, but don't fail if not json
                    response.raise_for_status() # Optional: decide if we want to fail on 4xx/5xx here or just return status
                except httpx.HTTPStatusError:
                    pass # We return status code, user can check it
                
                try:
                    data = response.json()
                except:
                    data = response.text
                    
                return {
                    "status": response.status_code,
                    "data": data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            raise RuntimeError(f"HTTP Request failed: {str(e)}")
