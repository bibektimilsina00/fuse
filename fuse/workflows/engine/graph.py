from typing import Any, Dict, List, Optional
from fuse.workflows.models import WorkflowNode

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
    @staticmethod
    def detect_cycles(nodes: List[WorkflowNode], edges: List[Any]) -> List[List[str]]:
        """
        Detect cycles in the workflow graph.
        Returns a list of cycles (each cycle is a list of node IDs).
        """
        adj = WorkflowGraph.build_adjacency_list(nodes, edges)
        visited = set()
        recursion_stack = set()
        cycles = []
        path = []

        def dfs(node_id):
            visited.add(node_id)
            recursion_stack.add(node_id)
            path.append(node_id)

            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in recursion_stack:
                    # Cycle detected
                    cycle_start_index = path.index(neighbor)
                    cycles.append(path[cycle_start_index:].copy())

            recursion_stack.remove(node_id)
            path.pop()

        for node in nodes:
            if node.node_id not in visited:
                dfs(node.node_id)
        
        return cycles

    @staticmethod
    def get_execution_order(nodes: List[WorkflowNode], edges: List[Any]) -> List[WorkflowNode]:
        """
        Get a topologically sorted list of nodes for execution order.
        Raises ValueError if a cycle is detected.
        """
        cycles = WorkflowGraph.detect_cycles(nodes, edges)
        if cycles:
            raise ValueError(f"Workflow contains cycles: {cycles}")

        adj = WorkflowGraph.build_adjacency_list(nodes, edges)
        visited = set()
        stack = []

        def topological_sort_util(node_id):
            visited.add(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    topological_sort_util(neighbor)
            stack.append(node_id)

        for node in nodes:
            if node.node_id not in visited:
                topological_sort_util(node.node_id)

        # Stack contains nodes in reverse topological order
        order_ids = stack[::-1]
        
        # specific optimization: ensure start nodes are first if possible (they should be naturally)
        
        # Map IDs back to objects
        node_map = {n.node_id: n for n in nodes}
        return [node_map[nid] for nid in order_ids if nid in node_map]
