from .crud_workflow import CRUDWorkflow

# Create a crud object similar to the original structure
class CRUD:
    def __init__(self):
        from .models import Workflow
        self.workflow = CRUDWorkflow(Workflow)

crud = CRUD()
