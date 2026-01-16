from typing import Any, Dict
import httpx
from fuse.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from fuse.workflows.engine.nodes.registry import NodeRegistry
from fuse.credentials.service import resolve_secret

@NodeRegistry.register
class DiscordSendNode(BaseNode):
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="discord.send",
            label="Discord Webhook",
            type="action",
            description="Post a message to a Discord channel via Webhook.",
            category="Communication",
            inputs=[
                NodeInput(name="webhook_url", type="credential", label="Webhook URL", required=True),
                NodeInput(name="content", type="string", label="Message Text", required=True),
                NodeInput(name="username", type="string", label="Bot Name", default="Automation Bot"),
                NodeInput(name="avatar_url", type="string", label="Avatar URL"),
                NodeInput(name="tts", type="boolean", label="Text-to-Speech", default=False)
            ],
            outputs=[
                NodeOutput(name="success", type="boolean", label="Success")
            ],
            error_policy="continue"
        )

    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        config = context.get("node_config", {})
        
        # Merge input data with config for dynamic overrides
        # Resolve 'webhook_url' whether it comes from config (credential ID) or runtime input
        url_raw = config.get("webhook_url") or input_data.get("webhook_url")
        url = resolve_secret(url_raw)

        content = config.get("content") or input_data.get("content")
        username = config.get("username", "Automation Bot")
        avatar_url = config.get("avatar_url")
        tts = config.get("tts", False)

        if not url:
            raise ValueError("Discord Webhook URL is required")
        
        payload = {
            "content": content,
            "username": username,
            "tts": tts
        }
        if avatar_url:
            payload["avatar_url"] = avatar_url

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            
        return {"success": True}
