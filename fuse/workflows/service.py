import uuid
import json
from typing import List
from datetime import datetime

from sqlmodel import Session

from fuse.workflows import crud
from fuse.workflows.models import Workflow, WorkflowNode, WorkflowEdge
from fuse.workflows.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowPublic,
    WorkflowSaveRequest,
    AIWorkflowRequest,
    AIWorkflowResponse
)



class WorkflowService:
    @staticmethod
    def create_workflow(
        *, session: Session, workflow_in: WorkflowCreate, owner_id: uuid.UUID
    ) -> Workflow:
        return crud.workflow.create_with_owner(
            session=session, obj_in=workflow_in, owner_id=owner_id
        )

    @staticmethod
    def get_workflow(session: Session, workflow_id: uuid.UUID) -> Workflow | None:
        return crud.workflow.get(session=session, id=workflow_id)

    @staticmethod
    def get_workflow_with_nodes(session: Session, workflow_id: uuid.UUID) -> Workflow | None:
        workflow = crud.workflow.get(session=session, id=workflow_id)
        if workflow:
            # Force load relationships to avoid lazy loading in async context
            _ = workflow.nodes
            _ = workflow.edges
        return workflow

    @staticmethod
    def get_workflows(session: Session, *, skip: int = 0, limit: int = 100) -> list[Workflow]:
        return crud.workflow.get_multi(session=session, skip=skip, limit=limit)

    @staticmethod
    def get_workflows_by_owner(
        session: Session,
        *,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Workflow]:
        return crud.workflow.get_multi_by_owner(
            session=session, owner_id=owner_id, skip=skip, limit=limit
        )

    @staticmethod
    def update_workflow(*, session: Session, db_workflow: Workflow, workflow_in: WorkflowUpdate) -> Workflow:
        db_workflow.updated_at = datetime.utcnow()
        return crud.workflow.update(session=session, db_obj=db_workflow, obj_in=workflow_in)

    @staticmethod
    def delete_workflow(*, session: Session, workflow_id: uuid.UUID) -> Workflow:
        return crud.workflow.remove(session=session, id=workflow_id)

    @staticmethod
    def count_workflows(session: Session) -> int:
        return crud.workflow.count(session=session)

    @staticmethod
    def count_workflows_by_owner(session: Session, *, owner_id: uuid.UUID) -> int:
        return crud.workflow.count_by_owner(session=session, owner_id=owner_id)
    
    @staticmethod
    def save_workflow_nodes(
        session: Session,
        *,
        workflow_id: uuid.UUID,
        save_request: WorkflowSaveRequest
    ) -> Workflow:
        """Save workflow nodes and edges using V2 structure"""
        return crud.workflow.save_workflow_nodes(
            session=session,
            workflow_id=workflow_id,
            workflow_data=save_request.model_dump()
        )
    
    @staticmethod
    def workflow_to_public(workflow: Workflow) -> WorkflowPublic:
        """Convert Workflow model to V2 WorkflowPublic schema"""
        from fuse.workflows.engine.nodes.registry import NodeRegistry
        
        # Meta
        tags = json.loads(workflow.tags) if workflow.tags else []
        meta = {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "version": "1.0.0",
            "status": workflow.status,
            "tags": tags,
            "owner": {"user_id": str(workflow.owner_id)},
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat()
        }
        
        # Graph - Nodes
        nodes = []
        for node in workflow.nodes:
            # Get node package from registry
            node_package = NodeRegistry.get_node(node.node_type)
            
            # Determine kind (trigger, action, logic)
            kind = "action"
            if node_package:
                category = node_package.manifest.get("category", "")
                if category == "triggers":
                    kind = "trigger"
                elif category in ["logic", "flow"]:
                    kind = "logic"
            
            # Ensure spec is valid V2 (Rule 7)
            spec = node.spec or {}
            if "node_name" not in spec:
                spec["node_name"] = node.node_type
            
            if "runtime" not in spec:
                runtime_type = "internal"
                # If we had special runtime support in manifest, we could read it here
                spec["runtime"] = {"type": runtime_type}
            
            if "config" not in spec:
                spec["config"] = {}
            
            nodes.append({
                "id": node.node_id,
                "kind": kind,
                "ui": {
                    "label": node.label,
                    "icon": node.icon,
                    "icon_svg": node_package.manifest.get("icon_svg") if node_package else None,
                    "position": {"x": node.position_x, "y": node.position_y}
                },
                "spec": spec
            })
        
        # Graph - Edges
        edges = [
            {
                "id": edge.edge_id,
                "source": edge.source,
                "target": edge.target,
                "condition": edge.label,
                "sourceHandle": edge.source_handle,
                "targetHandle": edge.target_handle
            }
            for edge in workflow.edges
        ]
        
        return WorkflowPublic(
            id=workflow.id,
            owner_id=workflow.owner_id,
            meta=meta,
            graph={"nodes": nodes, "edges": edges},
            execution=workflow.execution_config or {"mode": "async"},
            observability=workflow.observability_config or {"logging": True, "metrics": True},
            ai=workflow.ai_metadata or {"generated_by": "workflow-ai"}
        )


workflow_service = WorkflowService()
