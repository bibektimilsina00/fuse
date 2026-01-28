from typing import Any, Dict, List, Optional
from fuse.workflows.engine.definitions import WorkflowItem
from fuse.workflows.engine.expressions.resolver import ExpressionResolver

class NodeContext:
    """
    Execution context for a node.
    
    This class prepares the data structure expected by the execution engine and the node.
    It builds the context for the ExpressionResolver (variables, previous node results)
    and provides methods to resolve configuration values.
    """
    
    def __init__(
        self, 
        execution_id: str, 
        workflow_id: str,
        node_id: str,
        config: Dict[str, Any], 
        input_data: Any, # Can be Dict (V1) or List[WorkflowItem] (V2)
        results_map: Dict[str, Any],
        env: Dict[str, str] = None
    ):
        self.execution_id = execution_id
        self.workflow_id = workflow_id
        self.node_id = node_id
        self.raw_config = config
        self.input_data = input_data
        
        # Build the context dictionary for Jinja2
        # Structure:
        # $node["NodeName"].json["field"]
        # $input -> direct access to input data
        # $env -> environment variables
        
        self.expr_context = {
            "node": self._build_node_context(results_map),
            "input": input_data,
            "env": env or {},
            "execution": {
                "id": execution_id,
                "workflow_id": workflow_id
            }
        }
        
        self.resolver = ExpressionResolver(self.expr_context)

    def _build_node_context(self, results_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts the flat results map into the $node structure.
        """
        # Current results_map is { "node_id": output_data }
        # We want to support accessing by Node Name too if possible, but ID is primary for now.
        # Ideally, we should look up Node Name from ID, but we don't have the graph here easily
        # without querying the DB or passing the full workflow object.
        # For now, we map node_id -> { "json": data }
        
        node_ctx = {}
        for nid, data in results_map.items():
            # Ensure data is wrapped in the expected structure if accessing via .json
            # Use 'json' key for consistency with n8n standard
            node_ctx[nid] = {
                "json": data if isinstance(data, dict) else {"data": data},
                # For backward compat, allow direct access if it's not conflicting?
                # No, strict structure is better: $node.ID.json.field
            }
            
        return node_ctx

    def resolve_config(self) -> Dict[str, Any]:
        """
        Returns the configuration dictionary with all expressions resolved.
        """
        return self.resolver.resolve(self.raw_config)

    def resolve_inputs(self) -> Any:
        """
        Returns the inputs with all expressions resolved.
        """
        return self.resolver.resolve(self.input_data)
