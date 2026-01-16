class EngineError(Exception):
    """Base class for all engine errors."""
    pass

class WorkflowNotFoundError(EngineError):
    """Raised when a workflow is not found."""
    pass

class ExecutionNotFoundError(EngineError):
    """Raised when an execution is not found."""
    pass

class NodeNotFoundError(EngineError):
    """Raised when a node is not found in the workflow."""
    pass

class UnknownNodeTypeError(EngineError):
    """Raised when a node type is not registered."""
    pass
