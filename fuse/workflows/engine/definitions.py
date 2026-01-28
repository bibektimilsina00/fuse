from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class WorkflowItem(BaseModel):
    """
    Standard unit of data passed between nodes.
    
    Equivalent to n8n's item structure.
    Ensures that binary data (files) are always separated from JSON data.
    """
    json_data: Dict[str, Any] = Field(default_factory=dict, alias="json")
    binary_data: Dict[str, Any] = Field(default_factory=dict, alias="binary")
    paired_item: Optional[str] = Field(None, alias="pairedItem") # For future lineage tracking

    class Config:
        populate_by_name = True
