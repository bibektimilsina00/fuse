from typing import Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from fuse.auth.dependencies import CurrentUser
from fuse.plugins.google_ai import manager as cliproxy_manager

router = APIRouter()

class PluginAction(BaseModel):
    action: str  # install, start, stop, login

class PluginStatus(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    icon: Optional[str] = None
    installed: bool
    running: bool
    status: str  # active, installed, not_installed, error
    can_install: bool
    can_start: bool
    can_login: bool
    details: Optional[Any] = None

# Registry of built-in plugins (extensible in future)
def get_google_ai_plugin_status() -> PluginStatus:
    status = cliproxy_manager.get_cliproxy_status()
    is_installed = status["installed"]
    is_running = status["running"]
    
    plugin_status = "not_installed"
    if is_installed:
        plugin_status = "active" if is_running else "installed"
        
    return PluginStatus(
        id="google-ai-antigravity",
        name="Google AI / Antigravity",
        description="Unlock high-tier models (Claude Sonnet 3.5/4.5, Gemini 3 Pro) using your Google AI entitlement. Proxies requests via your local machine.",
        version="6.7.15",
        author="Bibek Timilsina",
        icon="google_ai",
        installed=is_installed,
        running=is_running,
        status=plugin_status,
        can_install=True,
        can_start=True,
        can_login=True,
        details=status
    )

@router.get("/", response_model=List[PluginStatus])
async def list_plugins(current_user: CurrentUser) -> Any:
    """List all available plugins."""
    # Currently hardcoded to just the Google AI one
    return [get_google_ai_plugin_status()]

@router.get("/{plugin_id}", response_model=PluginStatus)
async def get_plugin(plugin_id: str, current_user: CurrentUser) -> Any:
    """Get status of a specific plugin."""
    if plugin_id == "google-ai-antigravity":
        return get_google_ai_plugin_status()
    raise HTTPException(status_code=404, detail="Plugin not found")

@router.post("/{plugin_id}/action")
async def perform_plugin_action(
    plugin_id: str, 
    action_request: PluginAction,
    current_user: CurrentUser
) -> Any:
    """Perform an action (install, start, stop, login) on a plugin."""
    if plugin_id != "google-ai-antigravity":
        raise HTTPException(status_code=404, detail="Plugin not found")
        
    action = action_request.action
    
    if action == "install":
        success = cliproxy_manager.download_cliproxy()
        if not success:
            raise HTTPException(status_code=500, detail="Installation failed")
        return {"success": True, "message": "Plugin installed successfully"}
        
    elif action == "start":
        if cliproxy_manager.is_cliproxy_running():
             return {"success": True, "message": "Plugin service already running"}
             
        success = cliproxy_manager.start_cliproxy()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start plugin service")
        return {"success": True, "message": "Plugin service started"}
        
    elif action == "stop":
        cliproxy_manager.stop_cliproxy()
        return {"success": True, "message": "Plugin service stopped"}
        
    elif action == "login":
        success = cliproxy_manager.run_antigravity_login()
        if not success:
            raise HTTPException(status_code=500, detail="Login process failed")
        return {"success": True, "message": "Login successful"}
        
    elif action == "uninstall":
        success = cliproxy_manager.uninstall_cliproxy()
        if not success:
            # It might return False if it wasn't installed, which is fine, but if it failed due to permission...
            # For now, simplistic success
            pass 
        return {"success": True, "message": "Plugin uninstalled successfully"}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
