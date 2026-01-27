from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Body

from fuse.auth.dependencies import CurrentUser
from fuse.nodes.schemas import NodeResponse, NodeCreateRequest, NodeUpdateRequest
from fuse.nodes.service import node_management_service

router = APIRouter()

@router.get("/", response_model=List[NodeResponse])
async def list_nodes(
    current_user: CurrentUser
):
    """List all available nodes."""
    return node_management_service.list_nodes()

@router.get("/{node_id}", response_model=Dict[str, Any])
async def get_node(
    node_id: str,
    current_user: CurrentUser
):
    """Get details of a specific node."""
    return node_management_service.get_node(node_id)

@router.post("/create", response_model=Dict[str, Any])
async def create_node(
    request: NodeCreateRequest,
    current_user: CurrentUser
):
    """Create a new custom node."""
    return node_management_service.create_node(request)

@router.put("/{node_id}", response_model=Dict[str, Any])
async def update_node(
    node_id: str,
    request: NodeUpdateRequest,
    current_user: CurrentUser
):
    """Update an existing custom node."""
    return node_management_service.update_node(node_id, request)

@router.delete("/{node_id}")
async def delete_node(
    node_id: str,
    current_user: CurrentUser
):
    """Delete a custom node."""
    return node_management_service.delete_node(node_id)

@router.post("/{node_id}/icon")
async def upload_icon(
    node_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload an SVG icon for the node."""
    return await node_management_service.upload_icon(node_id, file)
