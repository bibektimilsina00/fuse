"""
Workflow Nodes Package

Dynamic package-based node system for workflow automation.

Nodes are loaded from node_packages/ directory as modular, self-contained packages.
This replaces the old class-based node system.
"""

from .loader import NodePackageLoader, NodePackage, get_node_loader, initialize_node_loader
from .registry import NodeRegistry

__all__ = [
    "NodePackageLoader",
    "NodePackage", 
    "NodeRegistry",
    "get_node_loader",
    "initialize_node_loader"
]
