# Central models file - Import all models here for Alembic migrations

# Import all SQLModel models so Alembic can detect them
from fuse.auth.models import User  # noqa: F401
from fuse.workflows.models import Workflow, WorkflowNode, WorkflowEdge  # noqa: F401
from fuse.credentials.models import Credential  # noqa: F401

# Add future models here as you create new modules
# from fuse.templates.models import Template  # noqa: F401
# from fuse.executions.models import Execution  # noqa: F401

