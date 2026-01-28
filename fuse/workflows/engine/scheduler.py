import logging
import uuid
from typing import Any, Dict, List
from sqlmodel import select
from fuse.workflows.engine.state import WorkflowState
from fuse.workflows.engine.graph import WorkflowGraph
from fuse.workflows.logger import WorkflowExecutorLogger
from fuse.workflows.models import NodeExecution

logger = logging.getLogger(__name__)

class WorkflowScheduler:
    def __init__(self, workflow_id: uuid.UUID, execution_id: uuid.UUID):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.state = WorkflowState(workflow_id, execution_id)
        self.logger = WorkflowExecutorLogger(workflow_id, execution_id)

    def start_workflow(self, trigger_data: Dict[str, Any] = None):
        """Start the workflow execution."""
        from fuse.workflows.engine.executor import WorkflowExecutor
        
        with self.state.get_session() as session:
            workflow = self.state.get_workflow(session)
            self.state.update_execution_status(session, "running", trigger_data)
            self.logger.log_workflow_start()

            # Rule 4 & 6: Validate DAG Structure before execution
            # This prevents infinite loops in malformed workflows
            try:
                WorkflowGraph.get_execution_order(workflow.nodes, workflow.edges)
            except ValueError as e:
                self.logger.log_workflow_failed(f"Invalid Workflow Structure: {str(e)}")
                self.state.update_execution_status(session, "failed")
                return

            start_nodes = WorkflowGraph.get_start_nodes(workflow.nodes, workflow.edges)
            
            if not start_nodes:
                self.logger.log_workflow_failed("No start nodes found (orphaned graph)")
                self.state.update_execution_status(session, "failed")
                return

            for node in start_nodes:
                self.schedule_node(node.node_id, trigger_data)

    def schedule_node(self, node_id: str, input_data: Any):
        """Schedule a node for execution."""
        from fuse.workflows.engine.executor import WorkflowExecutor
        
        logger.info(f"Scheduling node {node_id} for execution {self.execution_id}")
        
        with self.state.get_session() as session:
            workflow = self.state.get_workflow(session)
            node = WorkflowGraph.get_node_by_id(workflow.nodes, node_id)
            if not node:
                logger.error(f"Node {node_id} not found in workflow {self.workflow_id}")
                return

            node_execution = self.state.create_node_execution(session, node_id, node.node_type, input_data)
            self.logger.log_node_scheduled(node_id, str(node_execution.id))

            WorkflowExecutor.dispatch_node_task(self.execution_id, node_execution.id, node.node_type)

    def handle_node_completion(self, node_execution_id: uuid.UUID, output_data: Any):
        """Handle node completion and schedule next nodes based on logic."""
        with self.state.get_session() as session:
            node_execution = session.get(NodeExecution, node_execution_id)
            if not node_execution:
                return

            workflow = self.state.get_workflow(session)
            
            # Find next nodes
            next_nodes_to_schedule = []
            
            # Identify branching/looping logic
            node_type = str(node_execution.node_type).lower()
            
            # 1. Condition/Choice Nodes (1 Match Only)
            if node_type in ["logic.if", "condition.if", "condition.switch", "if", "switch"]:
                # Ensure output_data is usable (handle WorkflowItem list)
                data_dict = {}
                if isinstance(output_data, dict):
                    data_dict = output_data
                elif isinstance(output_data, list) and output_data:
                    # V2: Use first item for logic decision (unless loop)
                    first_item = output_data[0]
                    if hasattr(first_item, "json_data"):
                        data_dict = first_item.json_data
                    elif isinstance(first_item, dict):
                        data_dict = first_item

                # Determine which branch to take
                if node_type in ["condition.switch", "switch"]:
                    matched_branch = str(data_dict.get("matched", "default")).lower()
                else:
                    # For If nodes, check result or branch_taken
                    res = data_dict.get("result")
                    if res is None:
                        res = data_dict.get("matched")
                    
                    # Convert result to branch label
                    matched_branch = "true" if res else "false"
                
                # Allow nodes to specify data to pass, or pass the full output
                # In V2, we pass the full List[WorkflowItem] usually
                data_to_pass = output_data
                
                found_match = False
                outgoing_edges = [e for e in workflow.edges if e.source == node_execution.node_id]
                
                logger.info(f"Logic Node {node_execution.node_id} ({node_type}) produced branch: '{matched_branch}'. Outgoing edges: {len(outgoing_edges)}")
                
                for edge in outgoing_edges:
                    # Satisfy the match using label, handle, or ID
                    edge_label = str(edge.label or "").lower().strip()
                    id_lower = str(edge.edge_id or "").lower()
                    
                    is_match = False
                    if edge_label == matched_branch:
                        is_match = True
                    elif not edge_label:
                        if f"-{matched_branch}-" in id_lower or id_lower.endswith(f"-{matched_branch}"):
                            is_match = True
                        elif len(outgoing_edges) == 1:
                            is_match = True

                    if is_match:
                        logger.info(f"Logic match found! Path: {edge.source} -> {edge_label or 'default'} -> {edge.target}")
                        next_nodes_to_schedule.append((edge.target, data_to_pass))
                        found_match = True
                
                if not found_match:
                    logger.warning(f"CRITICAL: Logic node {node_execution.node_id} produced '{matched_branch}' but NO edge matched. Available edges IDs: {[e.edge_id for e in outgoing_edges]}")
            
            # 2. Iteration Nodes (Fan-out)
            elif node_type in ["logic.loop", "loop", "data.loop"]:
                # Support fanning out executions for each item in the loop
                items = []
                
                # V2: Handle List[WorkflowItem] directly
                if isinstance(output_data, list):
                    for item in output_data:
                        if hasattr(item, "json_data"):
                            items.append(item.json_data)
                        else:
                            items.append(item)
                
                # Fallback for old Dict structure
                elif isinstance(output_data, dict):
                     data_dict = output_data
                     items = data_dict.get("items", []) or data_dict.get("data", [])
                     if not isinstance(items, list) and items:
                         items = [items]

                # Ensure we have a list
                if not isinstance(items, list):
                    items = []

                logger.info(f"Loop Node {node_execution.node_id} fanning out {len(items)} executions.")
                
                for i, item in enumerate(items):
                    # Inject loop metadata into the payload
                    loop_payload = output_data.copy() if isinstance(output_data, dict) else {"data": output_data}
                    loop_payload.update({
                        "loop": {
                            "item": item,
                            "index": i,
                            "total": len(items)
                        },
                        "item": item # Convenience field
                    })
                    
                    for edge in workflow.edges:
                        if edge.source == node_execution.node_id:
                            next_nodes_to_schedule.append((edge.target, loop_payload))
            
            # 3. Default Linear Nodes (1:1 Flow)
            else:
                for edge in workflow.edges:
                    if edge.source == node_execution.node_id:
                        next_nodes_to_schedule.append((edge.target, output_data))
            
            for target_id, data in next_nodes_to_schedule:
                # Rule: Handle Fan-in/Merge synchronization
                target_node = WorkflowGraph.get_node_by_id(workflow.nodes, target_id)
                if target_node and (target_node.node_type == "logic.merge" or target_node.node_type == "ai.agent" or target_node.label == "Fan In"):
                    # 1. Identify all potential source IDs for this merge
                    incoming_edges = [e for e in workflow.edges if e.target == target_id]
                    source_ids = [e.source for e in incoming_edges]
                    
                    # 2. Check how many predecessors have already COMPLETED
                    completed_predecessors = session.exec(
                        select(NodeExecution.node_id)
                        .where(NodeExecution.workflow_execution_id == self.execution_id)
                        .where(NodeExecution.node_id.in_(source_ids))
                        .where(NodeExecution.status == "completed")
                    ).all()
                    unique_completed = set(completed_predecessors)
                    
                    # 3. Check for any currently active nodes in the ENTIRE workflow execution
                    # If there's at least one node still pending or running, we MUST wait 
                    # because it could lead to one of our missing predecessors.
                    active_nodes = self.state.get_active_node_executions(session)
                    
                    if len(unique_completed) < len(source_ids) and len(active_nodes) > 0:
                        logger.info(f"Fan-In Synchronization: Node {target_id} is waiting for other branches. "
                                    f"(Finished: {len(unique_completed)}/{len(source_ids)}, Active in workflow: {len(active_nodes)})")
                        continue
                    
                    # 4. Debounce check: ensure we don't start it multiple times if branches finish concurrently
                    existing_merge_exec = session.exec(
                        select(NodeExecution)
                        .where(NodeExecution.workflow_execution_id == self.execution_id)
                        .where(NodeExecution.node_id == target_id)
                        .where(NodeExecution.status.in_(["pending", "running", "completed"]))
                    ).first()
                    
                    if existing_merge_exec:
                        logger.info(f"Merge node {target_id} already scheduled or completed. Skipping duplicate trigger.")
                        continue
                    
                    logger.info(f"Fan-In Synchronization: All paths converged. Triggering {target_id}.")
                
                self.schedule_node(target_id, data)
            
            # Check for workflow completion
            active_nodes = self.state.get_active_node_executions(session)
            if not active_nodes and not next_nodes_to_schedule:
                # Only mark as completed if it hasn't failed or been cancelled already
                current_execution = self.state.get_execution(session)
                if current_execution.status not in ["completed", "failed", "cancelled"]:
                    self.state.update_execution_status(session, "completed")
                    self.logger.log_workflow_complete()
                    logger.info(f"Workflow execution {self.execution_id} completed successfully")
