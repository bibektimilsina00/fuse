import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Request

logger = logging.getLogger(__name__)
from pydantic import BaseModel
from src.auth.dependencies import CurrentUser, SessionDep
from src.utils.cache import CacheTTL, cache
from src.workflows.code_execution import router as code_execution_router
from src.workflows.models import WorkflowExecution
from src.workflows.schemas import (
    AIWorkflowRequest,
    AIWorkflowResponse,
    ExecuteNodeRequest,
    ExecuteNodeResponse,
    Message,
    TriggerWebhookResponse,
    WorkflowCreate,
    WorkflowExecutionPublic,
    WorkflowPublic,
    WorkflowSaveRequest,
    WorkflowsPublic,
    WorkflowUpdate,
)
from src.workflows.service import workflow_service
from starlette.concurrency import run_in_threadpool

router = APIRouter()

# Include code execution sub-router
router.include_router(code_execution_router, tags=["code-execution"])


@router.post("/{id}/execute", response_model=WorkflowExecutionPublic)
def execute_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    trigger_data: Dict[str, Any] = {},
) -> Any:
    """
    Execute a workflow immediately (test run).
    Creates an execution record and dispatches to Celery worker.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Create execution record first so we can return the ID immediately
    execution = WorkflowExecution(
        workflow_id=id, status="pending", trigger_data=str(trigger_data)
    )
    session.add(execution)
    session.commit()
    session.refresh(execution)

    # Dispatch to Celery worker with execution ID
    from src.workflows.engine import execute_workflow as execute_workflow_task

    execute_workflow_task.delay(str(id), trigger_data, str(execution.id))

    return execution


@router.get("/executions/{id}", response_model=WorkflowExecutionPublic)
def get_execution(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Get workflow execution by ID.
    """
    execution = session.get(WorkflowExecution, id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Check permissions (via workflow owner)
    # This requires joining or fetching workflow.
    # execution.workflow is loaded lazy usually, but let's check.
    if execution.workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return execution


@router.get("/", response_model=WorkflowsPublic)
def read_workflows(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve workflows owned by current user.
    """
    workflows = workflow_service.get_workflows_by_owner(
        session=session, owner_id=current_user.id, skip=skip, limit=limit
    )
    count = workflow_service.count_workflows_by_owner(
        session=session, owner_id=current_user.id
    )

    return WorkflowsPublic(
        data=[workflow_service.workflow_to_public(w) for w in workflows], count=count
    )


@router.get("/{id}", response_model=WorkflowPublic)
def read_workflow(
    id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get workflow by ID.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return workflow_service.workflow_to_public(workflow)


@router.post("/", response_model=WorkflowPublic)
def create_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    workflow_in: WorkflowCreate,
) -> Any:
    """
    Create new workflow.
    """
    workflow = workflow_service.create_workflow(
        session=session, workflow_in=workflow_in, owner_id=current_user.id
    )
    return workflow_service.workflow_to_public(workflow)


@router.patch("/{id}", response_model=WorkflowPublic)
def update_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    workflow_in: WorkflowUpdate,
) -> Any:
    """
    Update a workflow.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    workflow = workflow_service.update_workflow(
        session=session, db_workflow=workflow, workflow_in=workflow_in
    )
    return workflow_service.workflow_to_public(workflow)


@router.delete("/{id}", response_model=Message)
def delete_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Delete a workflow.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    workflow_service.delete_workflow(session=session, workflow_id=id)
    return Message(message="Workflow deleted successfully")


@router.post("/{id}/activate", response_model=WorkflowPublic)
def activate_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Activate a workflow to start listening for triggers.
    When active:
    - Schedule triggers will fire on their configured intervals
    - Webhook triggers will respond to incoming requests
    - Email/form triggers will listen for events
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update status to active
    workflow.status = "active"
    workflow.updated_at = datetime.utcnow()
    session.add(workflow)
    session.commit()
    session.refresh(workflow)

    return workflow_service.workflow_to_public(workflow)


@router.post("/{id}/deactivate", response_model=WorkflowPublic)
def deactivate_workflow(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Deactivate a workflow to stop listening for triggers.
    The workflow can still be executed manually via the Execute button.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Update status to inactive
    workflow.status = "inactive"
    workflow.updated_at = datetime.utcnow()
    session.add(workflow)
    session.commit()
    session.refresh(workflow)

    return workflow_service.workflow_to_public(workflow)


@router.post("/{id}/save", response_model=WorkflowPublic)
def save_workflow_nodes(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    save_request: WorkflowSaveRequest,
) -> Any:
    """
    Save workflow nodes and edges.
    """
    workflow = workflow_service.get_workflow(session=session, workflow_id=id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    workflow = workflow_service.save_workflow_nodes(
        session=session, workflow_id=id, save_request=save_request
    )
    return workflow_service.workflow_to_public(workflow)


@cache(ttl=CacheTTL.NODE_TYPES, prefix="node_types")
def _get_node_types_cached() -> List[Dict[str, Any]]:
    """Cached helper to get node type schemas."""
    import src.workflows.engine.nodes
    from src.workflows.engine.nodes.registry import NodeRegistry

    schemas = NodeRegistry.get_all_schemas()
    return [schema.model_dump() for schema in schemas]


@router.get("/nodes/types", response_model=List[Dict[str, Any]])
def get_node_types(
    current_user: CurrentUser,
) -> Any:
    """
    Get all available node types and their schemas.
    """
    return _get_node_types_cached()


class NodeOptionsRequest(BaseModel):
    node_type: str
    method_name: str
    dependency_values: Dict[str, Any]


@router.post("/node/options", response_model=List[Dict[str, str]])
async def get_node_options(
    request: NodeOptionsRequest,
    current_user: CurrentUser,
) -> Any:
    """
    Fetch dynamic options for a node input.
    """
    logger.debug(f"get_node_options called with: {request}")
    from src.workflows.engine.nodes.registry import NodeRegistry

    node_cls = NodeRegistry.get_node(request.node_type)
    if not node_cls:
        logger.debug(f"Unknown node type {request.node_type}")
        raise HTTPException(
            status_code=400, detail=f"Unknown node type: {request.node_type}"
        )

    node_instance = node_cls()

    if not hasattr(node_instance, request.method_name):
        raise HTTPException(
            status_code=400,
            detail=f"Method {request.method_name} not found on node {request.node_type}",
        )

    method = getattr(node_instance, request.method_name)
    if not callable(method):
        raise HTTPException(
            status_code=400, detail=f"Attribute {request.method_name} is not callable"
        )

    # Construct minimal context if needed, mostly for logging or user ID
    context = {"user_id": str(current_user.id)}

    try:
        options = await method(context, request.dependency_values)
        return options
    except Exception as e:
        logger.exception(f"Error fetching options: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/{workflow_id}", response_model=TriggerWebhookResponse)
async def trigger_webhook(
    workflow_id: uuid.UUID,
    request: Request,
    session: SessionDep,
) -> TriggerWebhookResponse:
    """
    Trigger a workflow via webhook.
    Only works if the workflow is active.
    """
    workflow = await run_in_threadpool(
        workflow_service.get_workflow_with_nodes,
        session=session,
        workflow_id=workflow_id,
    )
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Only active workflows respond to webhook triggers
    if workflow.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Workflow is not active. Activate it to enable webhook triggers.",
        )

    # Check if workflow has a webhook trigger
    import json

    nodes = workflow.nodes
    webhook_node = None
    for node in nodes:
        if node.node_type == "webhook.receive":
            webhook_node = node
            break

    if not webhook_node:
        raise HTTPException(
            status_code=400, detail="Workflow does not have a webhook trigger"
        )

    # Parse request data
    body = (
        await request.json()
        if request.headers.get("content-type") == "application/json"
        else await request.body()
    )
    if isinstance(body, bytes):
        try:
            body = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = body.decode("utf-8", errors="replace")

    headers = dict(request.headers)
    query = dict(request.query_params)
    method = request.method

    trigger_data = {
        "body": body,
        "headers": headers,
        "query": query,
        "method": method,
        "timestamp": str(datetime.utcnow()),
    }

    # Execute workflow
    from src.workflows.engine import execute_workflow as execute_workflow_task

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow_id, status="pending", trigger_data=json.dumps(trigger_data)
    )
    session.add(execution)
    session.commit()
    session.refresh(execution)

    task = execute_workflow_task.delay(
        str(workflow_id), trigger_data, str(execution.id)
    )

    return TriggerWebhookResponse(
        execution_id=execution.id,
        status="pending",
        message="Webhook received and workflow triggered",
    )


@router.post("/{id}/nodes/{node_id}/execute", response_model=ExecuteNodeResponse)
async def execute_node(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    node_id: str,
    request: ExecuteNodeRequest,
) -> ExecuteNodeResponse:
    """
    Execute a single node for testing purposes.
    Does not trigger downstream nodes or persist execution state.
    """
    workflow = await run_in_threadpool(
        workflow_service.get_workflow_with_nodes, session=session, workflow_id=id
    )
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Find node
    node = next((n for n in workflow.nodes if n.node_id == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    from src.workflows.engine.nodes.registry import NodeRegistry

    node_cls = NodeRegistry.get_node(node.node_type)
    if not node_cls:
        raise HTTPException(
            status_code=400, detail=f"Unknown node type: {node.node_type}"
        )

    input_data = request.input_data
    config_override = request.config

    try:
        node_instance = node_cls()

        # Use config override if provided, otherwise fallback to DB spec
        node_config = (
            config_override
            if config_override is not None
            else (
                node.spec.get("config", {})
                if (node.spec and isinstance(node.spec, dict))
                else {}
            )
        )

        logger.debug(f"Executing node {node_id}")
        logger.debug(f"Input: {input_data}")
        logger.debug(f"Config: {node_config}")

        context = {
            "workflow_id": str(workflow.id),
            "node_id": node.node_id,
            "node_config": node_config,
            "is_test": True,
        }

        # Execute node
        result = await node_instance.execute(context, input_data)
        return ExecuteNodeResponse(
            status="completed",
            result=result if isinstance(result, dict) else {"_output": result},
            node_id=node_id,
        )
    except Exception as e:
        logger.exception(f"Node execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Node execution failed: {str(e)}")


@router.get("/debug/workflows")
def list_debug_workflows():
    import os

    dummy_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dummy_json"
    )
    if not os.path.exists(dummy_dir):
        return []
    files = [f for f in os.listdir(dummy_dir) if f.endswith(".json")]
    return files


@router.get("/debug/workflows/{filename}")
def get_debug_workflow(filename: str):
    import json
    import os

    dummy_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "dummy_json"
    )
    file_path = os.path.join(dummy_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Workflow not found")
    with open(file_path, "r") as f:
        return json.load(f)


from fastapi import WebSocket, WebSocketDisconnect
from src.utils.redis_client import async_redis_client


@router.websocket("/ws/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    await websocket.accept()

    pubsub = async_redis_client.pubsub()
    channel = f"workflow:execution:{execution_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe(channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await pubsub.unsubscribe(channel)
