import os
import subprocess
import signal
import time
import httpx
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CLIPROXY_PORT = 8317
CLIPROXY_URL = f"http://127.0.0.1:{CLIPROXY_PORT}"
CLIPROXY_API_KEY = "fuse-local-dev-key"

def get_cliproxy_url():
    return CLIPROXY_URL

def get_cliproxy_api_key():
    return CLIPROXY_API_KEY

def is_cliproxy_running():
    try:
        with httpx.Client(timeout=1.0) as client:
            resp = client.get(f"{CLIPROXY_URL}/")
            return resp.status_code == 200
    except Exception:
        return False

def get_cliproxy_status():
    return {
        "installed": True, # Placeholder, should check if binary exists
        "running": is_cliproxy_running(),
        "url": CLIPROXY_URL,
        "port": CLIPROXY_PORT
    }

def start_cliproxy():
    if is_cliproxy_running():
        return True
    
    # In a real implementation, this would spawn the process
    # For now, we assume it's managed externally or we just return False
    # unless we have the binary path.
    logger.info("Starting CLIProxyAPI (placeholder implementation)")
    return False 

def stop_cliproxy():
    # Placeholder
    logger.info("Stopping CLIProxyAPI (placeholder implementation)")
    pass

def download_cliproxy():
    # Placeholder
    logger.info("Downloading CLIProxyAPI (placeholder implementation)")
    return True

def run_antigravity_login():
    # Placeholder
    logger.info("Running Antigravity Login (placeholder implementation)")
    return True

def uninstall_cliproxy():
    # Placeholder
    return True
