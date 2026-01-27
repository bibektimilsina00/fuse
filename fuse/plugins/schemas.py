from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class PluginCapabilities(BaseModel):
    can_install: bool = False
    can_start: bool = False
    can_stop: bool = False
    can_login: bool = False
    can_uninstall: bool = False

class PluginManifest(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    icon: Optional[str] = None
    capabilities: PluginCapabilities = PluginCapabilities()

class PluginStatus(PluginManifest):
    installed: bool = False
    running: bool = False
    status: str = "not_installed" # active, installed, not_installed, error
    details: Optional[Dict[str, Any]] = None

class PluginActionRequest(BaseModel):
    action: str # install, start, stop, uninstall, login, etc.
