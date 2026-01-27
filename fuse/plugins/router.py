from typing import List, Any
from fastapi import APIRouter, Depends
from fuse.auth.dependencies import CurrentUser
from fuse.plugins.schemas import PluginStatus, PluginActionRequest
from fuse.plugins.service import plugin_service

router = APIRouter()

@router.get("/", response_model=List[PluginStatus])
async def list_plugins(current_user: CurrentUser) -> Any:
    """List all available plugins."""
    return plugin_service.list_plugins()

@router.get("/{plugin_id}", response_model=PluginStatus)
async def get_plugin(plugin_id: str, current_user: CurrentUser) -> Any:
    """Get status of a specific plugin."""
    return plugin_service.get_plugin(plugin_id)

@router.post("/{plugin_id}/action")
async def perform_plugin_action(
    plugin_id: str, 
    action_request: PluginActionRequest,
    current_user: CurrentUser
) -> Any:
    """Perform an action (install, start, stop, login, etc.) on a plugin."""
    return plugin_service.perform_action(plugin_id, action_request)
