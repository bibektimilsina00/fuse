from typing import List, Dict, Any
from fastapi import HTTPException

from fuse.plugins.registry import plugin_registry
from fuse.plugins.schemas import PluginStatus, PluginActionRequest

class PluginService:
    def __init__(self):
        # Ensure registry is initialized
        if not plugin_registry.plugins:
            plugin_registry.initialize()

    def list_plugins(self) -> List[PluginStatus]:
        plugin_packages = plugin_registry.list_plugins()
        results = []
        for pkg in plugin_packages:
            if pkg.backend_module and hasattr(pkg.backend_module, "get_status"):
                # Dynamic status
                status_data = pkg.backend_module.get_status(pkg.manifest_data)
                results.append(PluginStatus(**status_data))
            else:
                # Static status (fallback)
                results.append(PluginStatus(**pkg.manifest_data, installed=False, running=False, status="unknown"))
        return results

    def get_plugin(self, plugin_id: str) -> PluginStatus:
        pkg = plugin_registry.get_plugin(plugin_id)
        if not pkg:
            raise HTTPException(status_code=404, detail="Plugin not found")
            
        if pkg.backend_module and hasattr(pkg.backend_module, "get_status"):
            status_data = pkg.backend_module.get_status(pkg.manifest_data)
            return PluginStatus(**status_data)
        
        return PluginStatus(**pkg.manifest_data)

    def perform_action(self, plugin_id: str, request: PluginActionRequest) -> Dict[str, Any]:
        pkg = plugin_registry.get_plugin(plugin_id)
        if not pkg:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        if not pkg.backend_module:
             raise HTTPException(status_code=500, detail="Plugin has no backend module loaded")

        action = request.action
        
        try:
            if action == "install":
                if hasattr(pkg.backend_module, "install"):
                    success = pkg.backend_module.install()
                    if not success: throw_error("Installation failed")
                    return {"success": True, "message": "Installed successfully"}
            
            elif action == "start":
                if hasattr(pkg.backend_module, "start"):
                    success = pkg.backend_module.start()
                    if not success: throw_error("Start failed")
                    return {"success": True, "message": "Started successfully"}

            elif action == "stop":
                if hasattr(pkg.backend_module, "stop"):
                    pkg.backend_module.stop()
                    return {"success": True, "message": "Stopped successfully"}

            elif action == "uninstall":
                 if hasattr(pkg.backend_module, "uninstall"):
                    pkg.backend_module.uninstall()
                    return {"success": True, "message": "Uninstalled successfully"}
            
            # Custom actions
            if hasattr(pkg.backend_module, "perform_custom_action"):
                return pkg.backend_module.perform_custom_action(action)
            
            raise HTTPException(status_code=400, detail=f"Action '{action}' not supported by this plugin")

        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))

def throw_error(msg):
    raise Exception(msg)

plugin_service = PluginService()
