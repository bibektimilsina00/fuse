from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class RuntimeType(str, Enum):
    INTERNAL = "internal"
    HTTP = "http"
    CODE = "code"

class ErrorPolicy(str, Enum):
    STOP = "stop"
    CONTINUE = "continue"
    RETRY = "retry"

class NodeInput(BaseModel):
    name: str
    type: str  # string, number, boolean, json, select, code, credential
    label: str
    required: bool = True
    default: Any = None
    options: Optional[List[Dict[str, Any]]] = None # For select type
    dynamic_options: Optional[str] = None # Name of method to fetch options dynamically: 'list_channels'
    dynamic_dependencies: Optional[List[str]] = None # List of input names this field depends on
    description: Optional[str] = None
    credential_type: Optional[str] = None  # For credential type: 'google_sheets', 'slack', 'whatsapp', etc.
    show_if: Optional[Dict[str, Any]] = None # Conditional visibility: { "spreadsheet_id": "NEW" }

class NodeOutput(BaseModel):
    name: str
    type: str
    label: str

class NodeSchema(BaseModel):
    name: str
    label: str
    type: str  # trigger, action, logic
    description: str
    inputs: List[NodeInput]
    outputs: List[NodeOutput]
    runtime: RuntimeType = RuntimeType.INTERNAL # Rule 6 & 7
    error_policy: ErrorPolicy = ErrorPolicy.STOP # Rule 7 & 8
    category: str = "Common"

class BaseNode(ABC):
    @property
    @abstractmethod
    def schema(self) -> NodeSchema:
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Any:
        """
        Execute the node logic.
        Rule 4: Deterministic, stateless at function level.
        Rule 10: Secrets/Config must be injected via context.
        """
        pass
