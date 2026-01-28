"""
Calculator Tool for AI Agents.
"""

from typing import Any, Dict, List
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Return calculator tool definition.
    """
    return [WorkflowItem(
        json={
            "tool": {
                "name": "calculator",
                "description": "Perform mathematical calculations. Input should be a valid math expression like '2 + 2' or 'sqrt(16)'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The math expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    )]

async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    return {"valid": True, "errors": []}
