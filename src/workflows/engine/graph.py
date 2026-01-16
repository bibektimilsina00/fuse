from typing import Any, Dict, List, Optional
from src.workflows.models import WorkflowNode

class WorkflowGraph:
    @staticmethod
    def build_adjacency_list(nodes: List[WorkflowNode], edges: List[Any]) -> Dict[str, List[str]]:
        """Build adjacency list for the graph."""
        adj_list = {node.node_id: [] for node in nodes}
        for edge in edges:
            source = getattr(edge, 'source', None)
            target = getattr(edge, 'target', None)
            if source and target and source in adj_list:
                adj_list[source].append(target)
        return adj_list

    @staticmethod
    def get_node_by_id(nodes: List[WorkflowNode], node_id: str) -> Optional[WorkflowNode]:
        for node in nodes:
            if node.node_id == node_id:
                return node
        return None

    @staticmethod
    def get_start_nodes(nodes: List[WorkflowNode], edges: List[Any]) -> List[WorkflowNode]:
        """Find nodes with no incoming edges."""
        incoming_counts = {node.node_id: 0 for node in nodes}
        for edge in edges:
            target = getattr(edge, 'target', None)
            if target in incoming_counts:
                incoming_counts[target] += 1
        
        return [node for node in nodes if incoming_counts[node.node_id] == 0]
