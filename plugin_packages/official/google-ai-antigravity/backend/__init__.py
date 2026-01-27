from . import manager

def get_status(manifest: dict) -> dict:
    """
    Get the dynamic status of the plugin combined with manifest data.
    """
    proxy_status = manager.get_cliproxy_status()
    installed = proxy_status["installed"]
    running = proxy_status["running"]
    
    status_str = "not_installed"
    if installed:
        status_str = "active" if running else "installed"
        
    return {
        **manifest,
        "installed": installed,
        "running": running,
        "status": status_str,
        "details": proxy_status
    }

def install() -> bool:
    return manager.download_cliproxy()

def start() -> bool:
    if manager.is_cliproxy_running():
        return True
    return manager.start_cliproxy()

def stop() -> bool:
    manager.stop_cliproxy()
    return True

def uninstall() -> bool:
    return manager.uninstall_cliproxy()

def perform_custom_action(action: str, **kwargs) -> dict:
    if action == "login":
        success = manager.run_antigravity_login()
        if not success:
             raise Exception("Login failed")
        return {"success": True, "message": "Login successful"}
    
    raise ValueError(f"Unknown custom action: {action}")
