import logging
from typing import Dict, Type, Optional
from fuse.workflows.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)

class NodeRegistry:
    _nodes: Dict[str, Type[BaseNode]] = {}

    @classmethod
    def register(cls, node_cls: Type[BaseNode]):
        schema = node_cls().schema
        cls._nodes[schema.name] = node_cls
        return node_cls

    @classmethod
    def get_node(cls, node_type: str) -> Optional[Type[BaseNode]]:
        return cls._nodes.get(node_type)

    @classmethod
    def list_nodes(cls):
        return {name: node.schema for name, node in cls._nodes.items()}

    @classmethod
    def get_all_schemas(cls):
        """Get schemas of all registered nodes."""
        return [node_cls().schema for node_cls in cls._nodes.values()]
