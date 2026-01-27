from typing import Any, Dict, List, Optional
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

class NodeManifestCreate(BaseModel):
    id: str = Field(..., description="Unique node ID (e.g. 'my.custom.node')")
    name: str
    version: str = "1.0.0"
    category: str = "custom"
    description: str = ""
    inputs: List[NodeInputSchema] = []
    outputs: List[NodeOutputSchema] = []
    tags: List[str] = []

class NodeCreateRequest(BaseModel):
    manifest: NodeManifestCreate
    code: str = Field(..., description="Python execution code for the node")

class NodeUpdateRequest(BaseModel):
    manifest: Optional[NodeManifestCreate] = None
    code: Optional[str] = None

class NodeResponse(BaseModel):
    id: str
    name: str
    version: str
    category: str
    description: str
    manifest: Dict[str, Any]
    is_custom: bool
    path: str
    has_icon: bool
