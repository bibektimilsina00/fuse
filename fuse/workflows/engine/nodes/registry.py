"""
Node Registry - New Package-Based System

This registry discovers and manages all workflow nodes from the node_packages directory.
It replaces the old class-based node system with a dynamic package-based approach.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from fuse.workflows.engine.nodes.loader import NodePackageLoader, NodePackage, initialize_node_loader, get_node_loader

logger = logging.getLogger(__name__)


class NodeRegistry:
    """
    Central registry for all workflow nodes.
    
    This NEW implementation loads nodes dynamically from node_packages/
    instead of using hardcoded Python classes with decorators.
    """
    
    _loader: Optional[NodePackageLoader] = None
    _initialized: bool = False
    
    @classmethod
    def initialize(cls, packages_dir: Optional[Path] = None):
        """
        Initialize the node registry by discovering all node packages.
        
        Args:
            packages_dir: Path to node_packages directory (default: auto-detect)
        """
        if cls._initialized:
            logger.warning("NodeRegistry already initialized")
            return
        
        if packages_dir is None:
            # Auto-detect: assume we're in fuse_backend/fuse/workflows/engine/nodes/
            current_file = Path(__file__)
            packages_dir = current_file.parent.parent.parent.parent.parent / "node_packages"
        
        logger.info(f"Initializing NodeRegistry from: {packages_dir}")
        cls._loader = initialize_node_loader(packages_dir)
        cls._initialized = True
        logger.info(f"NodeRegistry initialized with {len(cls._loader.loaded_nodes)} nodes")
    
    @classmethod
    def get_node(cls, node_type: str) -> Optional[NodePackage]:
        """
        Get a node package by its ID.
        
        Args:
            node_type: Node ID (e.g., "http.request")
            
        Returns:
            NodePackage instance or None
        """
        cls._ensure_initialized()
        return cls._loader.get_node(node_type)
    
    @classmethod
    def list_nodes(cls) -> Dict[str, Dict[str, Any]]:
        """
        List all available nodes with their metadata.
        
        Returns:
            Dict mapping node ID to node metadata
        """
        cls._ensure_initialized()
        nodes_list = cls._loader.list_nodes()
        return {node["id"]: node for node in nodes_list}
    
    @classmethod
    def get_all_schemas(cls) -> List[Dict[str, Any]]:
        """
        Get schemas of all registered nodes.
        
        This is used by the AI system for workflow generation.
        
        Returns:
            List of node schemas
        """
        cls._ensure_initialized()
        return cls._loader.get_all_schemas()
    
    @classmethod
    async def execute_node(
        cls,
        node_id: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a node.
        
        Args:
            node_id: Node ID to execute
            config: Node configuration
            inputs: Input data from previous nodes
            credentials: Optional credentials
            
        Returns:
            Node outputs
        """
        cls._ensure_initialized()
        return await cls._loader.execute_node(node_id, config, inputs, credentials)
    
    @classmethod
    def reload_node(cls, node_id: str) -> bool:
        """
        Reload a specific node (for development/hot-reload).
        
        Args:
            node_id: Node ID to reload
            
        Returns:
            True if successful
        """
        cls._ensure_initialized()
        return cls._loader.reload_node(node_id)
    
    @classmethod
    def reload_all(cls):
        """Reload all nodes from disk"""
        cls._initialized = False
        cls.initialize()
    
    @classmethod
    def _ensure_initialized(cls):
        """Ensure registry is initialized"""
        if not cls._initialized:
            cls.initialize()
    
    # =========================================================================
    # Deprecated Methods (for backward compatibility during transition)
    # =========================================================================
    
    @classmethod
    def register(cls, node_cls):
        """
        DEPRECATED: Old decorator-based registration.
        
        This is kept for backward compatibility but does nothing.
        All nodes should be in node_packages/ now.
        """
        logger.warning(
            f"NodeRegistry.register() is deprecated. "
            f"Move {node_cls.__name__} to node_packages/ instead."
        )
        return node_cls
