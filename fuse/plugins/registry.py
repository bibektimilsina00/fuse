import os
import json
import logging
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from fuse.plugins.schemas import PluginManifest, PluginStatus

logger = logging.getLogger(__name__)

class PluginPackage:
    def __init__(self, path: Path, manifest: dict, kind: str):
        self.path = path
        self.manifest_data = manifest
        self.kind = kind # 'official' or 'custom'
        self.id = manifest.get("id")
        self.backend_module = None

    def load_backend(self):
        backend_path = self.path / "backend" / "__init__.py"
        if backend_path.exists():
            try:
                module_name = f"plugin_packages.{self.kind}.{self.path.name}.backend"
                spec = importlib.util.spec_from_file_location(module_name, backend_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self.backend_module = module
            except Exception as e:
                logger.error(f"Failed to load backend for plugin {self.id}: {e}")

class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, PluginPackage] = {}
        self.base_path = Path(__file__).parent.parent.parent / "plugin_packages"
        
    def initialize(self):
        """Discover and load all plugins."""
        self.plugins = {}
        self._load_from_dir(self.base_path / "official", "official")
        self._load_from_dir(self.base_path / "custom", "custom")
        logger.info(f"Loaded {len(self.plugins)} plugins")

    def _load_from_dir(self, directory: Path, kind: str):
        if not directory.exists():
            return
            
        for item in directory.iterdir():
            if item.is_dir():
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest_data = json.load(f)
                            
                        # Basic validation
                        if "id" not in manifest_data:
                            logger.warning(f"Plugin at {item} missing 'id' in manifest")
                            continue
                            
                        package = PluginPackage(item, manifest_data, kind)
                        package.load_backend()
                        self.plugins[manifest_data["id"]] = package
                    except Exception as e:
                        logger.error(f"Error loading plugin from {item}: {e}")

    def list_plugins(self) -> List[PluginPackage]:
        return list(self.plugins.values())

    def get_plugin(self, plugin_id: str) -> Optional[PluginPackage]:
        return self.plugins.get(plugin_id)

plugin_registry = PluginRegistry()
