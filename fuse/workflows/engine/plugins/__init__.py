"""
Node Plugin System

Enables dynamic loading of workflow nodes from plugin packages.
"""

from .loader import NodePluginLoader, NodePlugin

__all__ = ["NodePluginLoader", "NodePlugin"]
