"""
Web Search Tool for AI Agents.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Return search tool definition.
    """
    config = context.resolve_config()
    
    return [WorkflowItem(
        json={
            "tool": {
                "name": "web_search",
                "description": "Search the web for real-time information, news, or factual data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                },
                "config": {
                    "engine": config.get("engine", "tavily"),
                    "max_results": config.get("max_results", 5)
                }
            }
        }
    )]

async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    return {"valid": True, "errors": []}
