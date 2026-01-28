from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class NodeInputSchema(BaseModel):
    name: str
    type: str  # string, number, boolean, select, json
    label: str
    required: bool = False
    default: Optional[Any] = None
    options: Optional[List[Dict[str, Any]]] = None  # For select inputs
    description: Optional[str] = None

class NodeOutputSchema(BaseModel):
    name: str
    type: str  # string, boolean, json, any
    label: str
    description: Optional[str] = None

from fuse.workflows.engine.nodes.schema import NodeInput, NodeOutput, NodeManifest

class NodeManifestCreate(NodeManifest):
    """
    V2 Manifest for creation.
    Inherits all strict V2 fields from engine schema.
    """
    pass

class NodeCreateRequest(BaseModel):
    manifest: NodeManifestCreate
    code: str = Field(..., description="Python execution code for the node")

class NodeUpdateRequest(BaseModel):
    manifest: Optional[NodeManifestCreate] = None
    code: Optional[str] = None

class NodeResponse(BaseModel):
    id: str
    name: str
    version: Union[int, str]
    nodeVersion: Optional[str] = None
    category: str
    description: str
    manifest: Dict[str, Any]
    is_custom: bool
    path: str
    has_icon: bool
