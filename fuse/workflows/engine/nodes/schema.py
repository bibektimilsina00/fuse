from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

# --- Enums ---
class NodeCategory(str, Enum):
    TRIGGER = "TRIGGER"
    ACTION = "ACTION"
    LOGIC = "LOGIC"
    UTILITY = "UTILITY"
    AI = "AI"
    AI_TOOL = "AI_TOOL"
    AI_ADAPTER = "AI_ADAPTER"

class ConnectionType(str, Enum):
    FLOW = "flow"
    AUXILIARY = "auxiliary"

# --- Models ---
class DisplayRule(BaseModel):
    """
    Defines a rule for showing a field.
    """
    model_config = ConfigDict(extra='allow')

class DisplayConfiguration(BaseModel):
    """
    Configuration for hiding/showing fields.
    """
    show: Optional[Dict[str, List[Any]]] = None
    hide: Optional[Dict[str, List[Any]]] = None

class TypeOptions(BaseModel):
    """
    Advanced options for specific input types.
    """
    loadOptionsMethod: Optional[str] = None
    loadOptionsDependsOn: Optional[List[str]] = None
    rows: Optional[int] = None
    language: Optional[str] = None
    
class SelectOption(BaseModel):
    label: str
    value: Any
    description: Optional[str] = None
    name: Optional[str] = None 

class NodeInput(BaseModel):
    """
    Definition of a single input field in the node.
    """
    name: str
    type: str # string, number, boolean, select, json, collection, etc.
    label: str
    default: Optional[Any] = None
    description: Optional[str] = None
    required: bool = False
    placeholder: Optional[str] = None
    
    # Polymorphic options: Select OR Nested inputs
    options: Optional[Union[List['NodeInput'], List[SelectOption], List[Dict[str, Any]]]] = None
    
    displayOptions: Optional[DisplayConfiguration] = None
    typeOptions: Optional[TypeOptions] = None 

class NodeOutput(BaseModel):
    name: str 
    type: str
    label: Optional[str] = None
    description: Optional[str] = None

class WebhookMethods(BaseModel):
    default: str = "default"
    start: Optional[str] = None
    stop: Optional[str] = None

class NodeManifest(BaseModel):
    """
    V2 Node Manifest Definition.
    Strictly typed for the new engine.
    """
    id: str
    version: int = 1
    nodeVersion: str = "1.0.0"
    
    name: Optional[str] = None
    displayName: Optional[str] = None
    
    description: str
    category: NodeCategory
    service: Optional[str] = "core"
    
    connectionType: ConnectionType = ConnectionType.FLOW
    
    icon: Optional[str] = None
    icon_svg: Optional[str] = None
    
    inputs: List[NodeInput] = []
    outputs: List[NodeOutput] = []
    
    webhook: bool = False
    webhookMethods: Optional[WebhookMethods] = None
    
    credentials: Optional[List[str]] = None
    tags: List[str] = []
    author: str = "Fuse"

    @field_validator("name", mode="before")
    def set_name_fallback(cls, v, values):
        if v is None and "id" in values.data:
            return values.data["id"]
        return v

    @field_validator("displayName", mode="before")
    def set_display_name(cls, v, values):
        if not v and "name" in values.data:
            return values.data["name"]
        return v
