"""
CLIProxyAPI Manager

Manages the CLIProxyAPI binary lifecycle:
- Downloads the appropriate binary for the user's platform on first use
- Starts/stops the proxy as a subprocess
- Generates configuration
"""

import os
import sys
import platform
import subprocess
import shutil
import logging
import time
import httpx
import yaml
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# CLIProxyAPI configuration
CLIPROXY_VERSION = "6.7.15"
CLIPROXY_GITHUB_REPO = "router-for-me/CLIProxyAPI"
CLIPROXY_PORT = 8317
CLIPROXY_API_KEY = "fuse-local-dev-key"

# Platform mappings
PLATFORM_MAP = {
    ("Darwin", "arm64"): "darwin_arm64",
    ("Darwin", "x86_64"): "darwin_amd64",
    ("Linux", "x86_64"): "linux_amd64",
    ("Linux", "aarch64"): "linux_arm64",
    ("Windows", "AMD64"): "windows_amd64",
    ("Windows", "ARM64"): "windows_arm64",
}


def get_fuse_data_dir() -> Path:
    """Get the Fuse data directory for storing binaries and config."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    fuse_dir = base / "fuse"
    fuse_dir.mkdir(parents=True, exist_ok=True)
    return fuse_dir


def get_cliproxy_dir() -> Path:
    """Get the directory for CLIProxyAPI binary and config."""
    cliproxy_dir = get_fuse_data_dir() / "cliproxyapi"
    cliproxy_dir.mkdir(parents=True, exist_ok=True)
    return cliproxy_dir


def get_cliproxy_binary_path() -> Path:
    """Get the path to the CLIProxyAPI binary."""
    binary_name = "cli-proxy-api.exe" if sys.platform == "win32" else "cli-proxy-api"
    return get_cliproxy_dir() / binary_name


def get_cliproxy_config_path() -> Path:
    """Get the path to the CLIProxyAPI config file."""
    return get_cliproxy_dir() / "config.yaml"


def get_platform_suffix() -> Optional[str]:
    """Get the platform suffix for downloading the correct binary."""
    system = platform.system()
    machine = platform.machine()
    return PLATFORM_MAP.get((system, machine))


def is_cliproxy_installed() -> bool:
    """Check if CLIProxyAPI is installed."""
    binary_path = get_cliproxy_binary_path()
    return binary_path.exists() and os.access(binary_path, os.X_OK)


def download_cliproxy() -> bool:
    """Download CLIProxyAPI binary for the current platform."""
    platform_suffix = get_platform_suffix()
    if not platform_suffix:
        logger.error(f"Unsupported platform: {platform.system()} {platform.machine()}")
        return False
    
    # Determine archive extension
    ext = "zip" if sys.platform == "win32" else "tar.gz"
    filename = f"CLIProxyAPI_{CLIPROXY_VERSION}_{platform_suffix}.{ext}"
    download_url = f"https://github.com/{CLIPROXY_GITHUB_REPO}/releases/download/v{CLIPROXY_VERSION}/{filename}"
    
    logger.info(f"Downloading CLIProxyAPI from {download_url}...")
    
    cliproxy_dir = get_cliproxy_dir()
    archive_path = cliproxy_dir / filename
    
    try:
        # Download the archive
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            response = client.get(download_url)
            response.raise_for_status()
            
            with open(archive_path, "wb") as f:
                f.write(response.content)
        
        logger.info(f"Downloaded to {archive_path}")
        
        # Extract the archive
        if ext == "tar.gz":
            import tarfile
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(cliproxy_dir)
        else:
            import zipfile
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(cliproxy_dir)
        
        # Make binary executable (Unix)
        binary_path = get_cliproxy_binary_path()
        if sys.platform != "win32":
            os.chmod(binary_path, 0o755)
        
        # Clean up archive
        archive_path.unlink()
        
        logger.info(f"CLIProxyAPI installed to {binary_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download CLIProxyAPI: {e}")
        if archive_path.exists():
            archive_path.unlink()
        return False


def generate_config() -> Path:
    """Generate CLIProxyAPI configuration file."""
    config_path = get_cliproxy_config_path()
    
    config = {
        "host": "127.0.0.1",
        "port": CLIPROXY_PORT,
        "auth-dir": str(Path.home() / ".cli-proxy-api"),
        "api-keys": [CLIPROXY_API_KEY],
        "debug": False,
        "request-retry": 3,
        "max-retry-interval": 30,
        "quota-exceeded": {
            "switch-project": True,
            "switch-preview-model": True,
        },
        "oauth-model-alias": {
            "antigravity": [
                {"name": "gemini-3-pro-high", "alias": "gemini-3-pro-preview"},
                {"name": "gemini-3-flash", "alias": "gemini-3-flash-preview"},
                {"name": "claude-sonnet-4-5", "alias": "gemini-claude-sonnet-4-5"},
                {"name": "claude-sonnet-4-5-thinking", "alias": "gemini-claude-sonnet-4-5-thinking"},
                {"name": "claude-opus-4-5-thinking", "alias": "gemini-claude-opus-4-5-thinking"},
            ]
        },
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Generated CLIProxyAPI config at {config_path}")
    return config_path


def is_cliproxy_running() -> bool:
    """Check if CLIProxyAPI is running by pinging the health endpoint."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"http://127.0.0.1:{CLIPROXY_PORT}/health")
            return resp.status_code == 200
    except:
        return False


# Global process reference
_cliproxy_process: Optional[subprocess.Popen] = None


def start_cliproxy() -> bool:
    """Start CLIProxyAPI as a subprocess."""
    global _cliproxy_process
    
    # Check if already running
    if is_cliproxy_running():
        logger.info("CLIProxyAPI is already running")
        return True
    
    # Install if needed
    if not is_cliproxy_installed():
        logger.info("CLIProxyAPI not found, downloading...")
        if not download_cliproxy():
            return False
    
    # Generate config if needed
    config_path = get_cliproxy_config_path()
    if not config_path.exists():
        generate_config()
    
    # Start the process
    binary_path = get_cliproxy_binary_path()
    
    try:
        # Start in background with output suppressed (or logged)
        log_file = get_cliproxy_dir() / "cliproxy.log"
        
        with open(log_file, "a") as log:
            _cliproxy_process = subprocess.Popen(
                [str(binary_path), "--config", str(config_path)],
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=str(get_cliproxy_dir()),
            )
        
        # Wait for it to start
        for _ in range(10):
            time.sleep(0.5)
            if is_cliproxy_running():
                logger.info(f"CLIProxyAPI started on port {CLIPROXY_PORT}")
                return True
        
        logger.error("CLIProxyAPI failed to start within timeout")
        return False
        
    except Exception as e:
        logger.error(f"Failed to start CLIProxyAPI: {e}")
        return False


def stop_cliproxy():
    """Stop CLIProxyAPI subprocess."""
    global _cliproxy_process
    
    if _cliproxy_process:
        try:
            _cliproxy_process.terminate()
            _cliproxy_process.wait(timeout=5)
            logger.info("CLIProxyAPI stopped")
        except subprocess.TimeoutExpired:
            _cliproxy_process.kill()
        except Exception as e:
            logger.error(f"Error stopping CLIProxyAPI: {e}")
        finally:
            _cliproxy_process = None


def run_antigravity_login() -> bool:
    """Run the Antigravity OAuth login flow."""
    if not is_cliproxy_installed():
        if not download_cliproxy():
            return False
    
    binary_path = get_cliproxy_binary_path()
    
    # Ensure config exists
    config_path = get_cliproxy_config_path()
    if not config_path.exists():
        generate_config()
    
    try:
        logger.info("Starting Antigravity OAuth login...")
        result = subprocess.run(
            [str(binary_path), "--config", str(config_path), "-antigravity-login"],
            cwd=str(get_cliproxy_dir()),
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Antigravity login failed: {e}")
        return False


def get_cliproxy_url() -> str:
    """Get the CLIProxyAPI base URL."""
    return f"http://127.0.0.1:{CLIPROXY_PORT}"


def get_cliproxy_api_key() -> str:
    """Get the CLIProxyAPI API key."""
    return CLIPROXY_API_KEY


def get_cliproxy_status() -> dict:
    """Get detailed status of CLIProxyAPI."""
    installed = is_cliproxy_installed()
    running = is_cliproxy_running()
    
    # Check for OAuth tokens
    auth_dir = Path.home() / ".cli-proxy-api"
    accounts = []
    if auth_dir.exists():
        for f in auth_dir.glob("antigravity-*.json"):
            accounts.append(f.name.replace("antigravity-", "").replace(".json", ""))
    
    return {
        "installed": installed,
        "running": running,
        "binary_path": str(get_cliproxy_binary_path()) if installed else None,
        "config_path": str(get_cliproxy_config_path()) if get_cliproxy_config_path().exists() else None,
        "port": CLIPROXY_PORT,
        "accounts": accounts,
    }
