"""
Node Plugin Loader

Dynamically discovers and loads node plugins from the node_packages directory.
This decouples nodes from the core codebase, enabling:
- Hot reload of nodes
- User-created nodes
- Plugin marketplace
- Version management
"""

import json
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NodePlugin:
    """Represents a loaded node plugin"""
    id: str
    name: str
    version: str
    manifest: Dict[str, Any]
    execute_fn: Callable
    validate_fn: Optional[Callable] = None
    plugin_dir: Path = None


class NodePluginLoader:
    """
    Loads and manages node plugins from the filesystem.
    
    Usage:
        loader = NodePluginLoader(Path("node_packages"))
        plugins = await loader.discover_plugins()
        result = await loader.execute_plugin("http.request", config, inputs)
    """
    
    def __init__(self, plugins_dir: Path):
        """
        Initialize the plugin loader.
        
        Args:
            plugins_dir: Root directory containing plugin packages
        """
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, NodePlugin] = {}
        
    def discover_plugins(self) -> List[NodePlugin]:
        """
        Scan the plugins directory and load all valid node packages.
        
        Returns:
            List of successfully loaded NodePlugin objects
        """
        plugins = []
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return plugins
        
        # Scan all subdirectories (official, community, custom)
        for category_dir in self.plugins_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            
            # Scan each plugin in the category
            for plugin_dir in category_dir.iterdir():
                if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                    continue
                
                manifest_path = plugin_dir / "manifest.json"
                if not manifest_path.exists():
                    logger.warning(f"Skipping {plugin_dir.name}: no manifest.json")
                    continue
                
                try:
                    plugin = self._load_plugin(plugin_dir)
                    plugins.append(plugin)
                    self.loaded_plugins[plugin.id] = plugin
                    logger.info(f"✓ Loaded plugin: {plugin.name} v{plugin.version} ({plugin.id})")
                except Exception as e:
                    logger.error(f"✗ Failed to load plugin {plugin_dir.name}: {e}", exc_info=True)
        
        logger.info(f"Loaded {len(plugins)} node plugins")
        return plugins
    
    def _load_plugin(self, plugin_dir: Path) -> NodePlugin:
        """
        Load a single plugin from its directory.
        
        Args:
            plugin_dir: Path to the plugin directory
            
        Returns:
            NodePlugin instance
            
        Raises:
            ValueError: If manifest is invalid or execution module missing
        """
        # Load and validate manifest
        with open(plugin_dir / "manifest.json", "r") as f:
            manifest = json.load(f)
        
        self._validate_manifest(manifest)
        
        # Load the execution module
        execute_module_path = plugin_dir / "backend" / "execute.py"
        if not execute_module_path.exists():
            raise ValueError(f"Missing backend/execute.py in {plugin_dir.name}")
        
        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(
            f"node_plugins.{manifest['id']}.execute",
            execute_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the execute function
        if not hasattr(module, "execute"):
            raise ValueError(f"Plugin {plugin_dir.name} missing execute() function")
        
        execute_fn = module.execute
        
        # Get optional validate function
        validate_fn = getattr(module, "validate", None)
        
        return NodePlugin(
            id=manifest["id"],
            name=manifest["name"],
            version=manifest["version"],
            manifest=manifest,
            execute_fn=execute_fn,
            validate_fn=validate_fn,
            plugin_dir=plugin_dir
        )
    
    def _validate_manifest(self, manifest: Dict[str, Any]) -> None:
        """
        Validate that manifest has required fields.
        
        Args:
            manifest: Parsed manifest.json dict
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["id", "name", "version", "inputs", "outputs"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Manifest missing required field: {field}")
    
    async def execute_plugin(
        self,
        plugin_id: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a loaded plugin with the given configuration.
        
        Args:
            plugin_id: ID of the plugin to execute (e.g., "http.request")
            config: Node configuration (url, method, etc.)
            inputs: Runtime input data from previous nodes
            credentials: Optional credentials for the plugin
            
        Returns:
            Dict with plugin outputs
            
        Raises:
            ValueError: If plugin not found or validation fails
            RuntimeError: If execution fails
        """
        plugin = self.loaded_plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found. Available: {list(self.loaded_plugins.keys())}")
        
        # Optional: Validate configuration before execution
        if plugin.validate_fn:
            validation_result = await plugin.validate_fn(config)
            if not validation_result.get("valid", True):
                errors = validation_result.get("errors", ["Validation failed"])
                raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        # Build execution context
        context = {
            "config": config,
            "inputs": inputs,
            "credentials": credentials,
            "plugin": {
                "id": plugin.id,
                "version": plugin.version
            }
        }
        
        # Execute the plugin
        try:
            result = await plugin.execute_fn(context)
            return result
        except Exception as e:
            logger.error(f"Plugin {plugin_id} execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Plugin execution failed: {str(e)}")
    
    def get_plugin(self, plugin_id: str) -> Optional[NodePlugin]:
        """Get a loaded plugin by ID"""
        return self.loaded_plugins.get(plugin_id)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        Get a list of all loaded plugins with their metadata.
        
        Returns:
            List of dicts with plugin information
        """
        return [
            {
                "id": plugin.id,
                "name": plugin.name,
                "version": plugin.version,
                "category": plugin.manifest.get("category", "uncategorized"),
                "description": plugin.manifest.get("description", ""),
                "inputs": plugin.manifest.get("inputs", []),
                "outputs": plugin.manifest.get("outputs", []),
                "author": plugin.manifest.get("author", "Unknown"),
                "tags": plugin.manifest.get("tags", [])
            }
            for plugin in self.loaded_plugins.values()
        ]
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """
        Reload a specific plugin (useful for development).
        
        Args:
            plugin_id: ID of plugin to reload
            
        Returns:
            True if reloaded successfully
        """
        plugin = self.loaded_plugins.get(plugin_id)
        if not plugin or not plugin.plugin_dir:
            return False
        
        try:
            new_plugin = self._load_plugin(plugin.plugin_dir)
            self.loaded_plugins[plugin_id] = new_plugin
            logger.info(f"Reloaded plugin: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload plugin {plugin_id}: {e}")
            return False
