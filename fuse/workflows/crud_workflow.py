import uuid
import json
from typing import List

from sqlmodel import Session, select

from fuse.base import CRUDBase
from fuse.workflows.models import Workflow, WorkflowNode, WorkflowEdge
from fuse.workflows.schemas import WorkflowCreate, WorkflowUpdate


class CRUDWorkflow(CRUDBase[Workflow, WorkflowCreate, WorkflowUpdate]):
    def create_with_owner(
        self, session: Session, *, obj_in: WorkflowCreate, owner_id: uuid.UUID
    ) -> Workflow:
        obj_in_data = obj_in.model_dump()
        db_obj = Workflow(**obj_in_data, owner_id=owner_id)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self,
        session: Session,
        *,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Workflow]:
        statement = (
            select(Workflow).where(Workflow.owner_id == owner_id).offset(skip).limit(limit)
        )
        return list(session.exec(statement).all())

    def count_by_owner(self, session: Session, *, owner_id: uuid.UUID) -> int:
        from sqlmodel import func

        statement = (
            select(func.count()).select_from(Workflow).where(Workflow.owner_id == owner_id)
        )
        return session.exec(statement).one()
    
    def save_workflow_nodes(
        self,
        session: Session,
        *,
        workflow_id: uuid.UUID,
        workflow_data: dict  # The full V2 JSON
    ) -> Workflow:
        """Save or update workflow nodes and edges using V2 structure"""
        workflow = session.get(Workflow, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with id {workflow_id} not found")
        
        # Update meta fields if provided
        meta = workflow_data.get("meta", {})
        if "name" in meta: workflow.name = meta["name"]
        if "description" in meta: workflow.description = meta["description"]
        if "status" in meta: workflow.status = meta["status"]
        if "tags" in meta: workflow.tags = json.dumps(meta["tags"])
        
        # Update config blobs
        workflow.execution_config = workflow_data.get("execution", {})
        workflow.observability_config = workflow_data.get("observability", {})
        workflow.ai_metadata = workflow_data.get("ai", {})
        
        # Delete existing nodes and edges
        for node in workflow.nodes:
            session.delete(node)
        for edge in workflow.edges:
            session.delete(edge)
        session.flush()
        
        graph = workflow_data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        # Create new nodes
        for node_data in nodes:
            # Map V2 -> WorkflowNode
            ui = node_data.get("ui", {})
            spec = node_data.get("spec", {})
            
            node = WorkflowNode(
                workflow_id=workflow_id,
                node_id=node_data["id"],
                node_type=spec.get("node_name", "manual_trigger"),
                position_x=ui.get("position", {}).get("x", 0),
                position_y=ui.get("position", {}).get("y", 0),
                label=ui.get("label", "Node"),
                icon=ui.get("icon"),
                spec=spec
            )
            session.add(node)
        
        # Create new edges
        for edge_data in edges:
            edge = WorkflowEdge(
                workflow_id=workflow_id,
                edge_id=edge_data["id"],
                source=edge_data["source"],
                target=edge_data["target"],
                label=edge_data.get("condition"),
                source_handle=edge_data.get("sourceHandle"),
                target_handle=edge_data.get("targetHandle")
            )
            session.add(edge)
        
        session.commit()
        session.refresh(workflow)
        return workflow


workflow = CRUDWorkflow(Workflow)
