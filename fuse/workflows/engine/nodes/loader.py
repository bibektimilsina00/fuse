"""
Node Package Loader

Dynamically loads workflow nodes from node_packages directory.
These are modular, packaged nodes - NOT to be confused with integration plugins.

Terminology:
- Node Package = Packaged workflow node (http-request, email-send, etc.)
- Plugin = Integration plugin (google_ai, oauth providers, etc.)
"""

import json
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NodePackage:
    """Represents a loaded node package"""
    id: str
    name: str
    version: str
    manifest: Dict[str, Any]
    execute_fn: Callable
    validate_fn: Optional[Callable] = None
    package_dir: Path = None


class NodePackageLoader:
    """
    Loads and manages packaged workflow nodes from the filesystem.
    
    Usage:
        loader = NodePackageLoader(Path("node_packages"))
        nodes = loader.discover_nodes()
        result = await loader.execute_node("http.request", config, inputs)
    """
    
    def __init__(self, packages_dir: Path):
        """
        Initialize the node loader.
        
        Args:
            packages_dir: Root directory containing node packages
        """
        self.packages_dir = Path(packages_dir)
        self.loaded_nodes: Dict[str, NodePackage] = {}
        
    def discover_nodes(self) -> List[NodePackage]:
        """
        Scan the packages directory and load all valid node packages.
        
        Returns:
            List of successfully loaded NodePackage objects
        """
        nodes = []
        
        if not self.packages_dir.exists():
            logger.warning(f"Node packages directory {self.packages_dir} does not exist")
            return nodes
        
        # Scan all subdirectories (official, community, custom)
        for category_dir in self.packages_dir.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue
            
            # Scan each node package in the category
            for package_dir in category_dir.iterdir():
                if not package_dir.is_dir() or package_dir.name.startswith("_"):
                    continue
                
                manifest_path = package_dir / "manifest.json"
                if not manifest_path.exists():
                    logger.warning(f"Skipping {package_dir.name}: no manifest.json")
                    continue
                
                try:
                    node_package = self._load_node_package(package_dir)
                    nodes.append(node_package)
                    self.loaded_nodes[node_package.id] = node_package
                    logger.info(f"✓ Loaded node: {node_package.name} v{node_package.version} ({node_package.id})")
                except Exception as e:
                    logger.error(f"✗ Failed to load node {package_dir.name}: {e}", exc_info=True)
        
        logger.info(f"Loaded {len(nodes)} workflow nodes")
        return nodes
    
    def _load_node_package(self, package_dir: Path) -> NodePackage:
        """
        Load a single node package from its directory.
        
        Args:
            package_dir: Path to the node package directory
            
        Returns:
            NodePackage instance
            
        Raises:
            ValueError: If manifest is invalid or execution module missing
        """
        # Load and validate manifest
        with open(package_dir / "manifest.json", "r") as f:
            manifest = json.load(f)
        
        self._validate_manifest(manifest)
        
        # Load the execution module
        execute_module_path = package_dir / "backend" / "execute.py"
        if not execute_module_path.exists():
            raise ValueError(f"Missing backend/execute.py in {package_dir.name}")
        
        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(
            f"node_packages.{manifest['id']}.execute",
            execute_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the execute function
        if not hasattr(module, "execute"):
            raise ValueError(f"Node package {package_dir.name} missing execute() function")
        
        execute_fn = module.execute
        
        # Get optional validate function
        validate_fn = getattr(module, "validate", None)
        
        # Load optional icon
        icon_path = package_dir / "frontend" / "icon.svg"
        if icon_path.exists():
            try:
                manifest["icon_svg"] = icon_path.read_text("utf-8")
            except Exception as e:
                logger.warning(f"Failed to read icon.svg for {manifest['id']}: {e}")

        return NodePackage(
            id=manifest["id"],
            name=manifest["name"],
            version=manifest["version"],
            manifest=manifest,
            execute_fn=execute_fn,
            validate_fn=validate_fn,
            package_dir=package_dir
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
    
    async def execute_node(
        self,
        node_id: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a loaded node package with the given configuration.
        
        Args:
            node_id: ID of the node to execute (e.g., "http.request")
            config: Node configuration (url, method, etc.)
            inputs: Runtime input data from previous nodes
            credentials: Optional credentials for the node
            
        Returns:
            Dict with node outputs
            
        Raises:
            ValueError: If node not found or validation fails
            RuntimeError: If execution fails
        """
        node_package = self.loaded_nodes.get(node_id)
        if not node_package:
            raise ValueError(f"Node '{node_id}' not found. Available: {list(self.loaded_nodes.keys())}")
        
        # Optional: Validate configuration before execution
        if node_package.validate_fn:
            validation_result = await node_package.validate_fn(config)
            if not validation_result.get("valid", True):
                errors = validation_result.get("errors", ["Validation failed"])
                raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        # Build execution context
        context = {
            "config": config,
            "inputs": inputs,
            "credentials": credentials,
            "node": {
                "id": node_package.id,
                "version": node_package.version
            }
        }
        
        # Execute the node
        try:
            result = await node_package.execute_fn(context)
            return result
        except Exception as e:
            logger.error(f"Node {node_id} execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Node execution failed: {str(e)}")
    
    def get_node(self, node_id: str) -> Optional[NodePackage]:
        """Get a loaded node package by ID"""
        return self.loaded_nodes.get(node_id)
    
    def list_nodes(self) -> List[Dict[str, Any]]:
        """
        Get a list of all loaded node packages with their metadata.
        
        Returns:
            List of dicts with node information
        """
        return [
            {
                "id": node.id,
                "name": node.name,
                "version": node.version,
                "category": node.manifest.get("category", "uncategorized"),
                "description": node.manifest.get("description", ""),
                "inputs": node.manifest.get("inputs", []),
                "outputs": node.manifest.get("outputs", []),
                "author": node.manifest.get("author", "Unknown"),
                "tags": node.manifest.get("tags", [])
            }
            for node in self.loaded_nodes.values()
        ]
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas of all loaded nodes (for compatibility with AI system).
        
        Returns:
            List of node schemas
        """
        schemas = []
        for node in self.loaded_nodes.values():
            manifest = node.manifest
            # Convert manifest to schema format
            schema = {
                "name": manifest["id"],
                "label": manifest["name"],
                "type": self._infer_type_from_category(manifest.get("category", "")),
                "description": manifest.get("description", ""),
                "category": manifest.get("category", ""),
                "inputs": manifest.get("inputs", []),
                "outputs": manifest.get("outputs", []),
                "icon": manifest.get("icon"),
                "icon_svg": manifest.get("icon_svg"),  # pass embedded SVG to frontend
            }
            schemas.append(schema)
        return schemas
    
    def _infer_type_from_category(self, category: str) -> str:
        """Map category to node type"""
        if category == "triggers":
            return "trigger"
        elif category in ["logic", "flow"]:
            return "logic"
        else:
            return "action"
    
    def reload_node(self, node_id: str) -> bool:
        """
        Reload a specific node package (useful for development).
        
        Args:
            node_id: ID of node to reload
            
        Returns:
            True if reloaded successfully
        """
        node = self.loaded_nodes.get(node_id)
        if not node or not node.package_dir:
            return False
        
        try:
            new_node = self._load_node_package(node.package_dir)
            self.loaded_nodes[node_id] = new_node
            logger.info(f"Reloaded node: {node_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload node {node_id}: {e}")
            return False


# Global instance (initialized on app startup)
_node_loader: Optional[NodePackageLoader] = None


def get_node_loader() -> NodePackageLoader:
    """Get the global node loader instance"""
    global _node_loader
    if _node_loader is None:
        raise RuntimeError("Node loader not initialized. Call initialize_node_loader() first.")
    return _node_loader


def initialize_node_loader(packages_dir: Path) -> NodePackageLoader:
    """Initialize the global node loader"""
    global _node_loader
    _node_loader = NodePackageLoader(packages_dir)
    _node_loader.discover_nodes()
    return _node_loader
