import asyncio
import uuid
from types import SimpleNamespace

import apps.api.app.shared.model  # noqa: F401
from apps.api.app.features.workflows.schemas import WorkflowCreate
from apps.api.app.features.workflows.service import WorkflowService


class FakeWorkflowRepository:
    def __init__(self):
        self.created_workflow = None

    async def create(self, workflow):
        self.created_workflow = workflow
        return workflow


def test_create_workflow_adds_manual_trigger_for_empty_graph():
    repository = FakeWorkflowRepository()
    service = WorkflowService.__new__(WorkflowService)
    service.repository = repository
    user = SimpleNamespace(id=uuid.uuid4())
    workspace = SimpleNamespace(id=uuid.uuid4())

    workflow = asyncio.run(
        service.create_workflow(WorkflowCreate(name="Test workflow"), user, workspace)
    )

    assert workflow.user_id == user.id
    assert workflow.workspace_id == workspace.id
    assert workflow.graph["edges"] == []
    assert workflow.graph["nodes"][0]["type"] == "trigger.manual"
    assert workflow.graph["nodes"][0]["data"]["properties"]["startWorkflow"] == "manual"
