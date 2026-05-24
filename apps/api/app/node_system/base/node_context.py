from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class NodeContext:
    execution_id: str
    workflow_id: str
    node_id: str
    variables: dict[str, Any]
    credentials: list[dict[str, Any]]
    http_client: httpx.AsyncClient
    db: AsyncSession | None = None
    emitter: Any = None  # IEventEmitter — injected by WorkflowRunner
    # Injected by WorkflowRunner: run this node's successor sub-graphs with given input.
    # Pre-bound to the current node's outgoing edge targets.
    # Returns list of output dicts (one per successor branch).
    run_downstream: Any = None  # async callable: (input_data: dict) -> list[dict]
    # Injected by WorkflowRunner: pause this execution (raises PauseSignal)
    pause: Any = None  # async callable: (resume_schema: dict) -> never

    def get_credential_data(
        self,
        credential_type: str | list[str],
        selected_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Return credential data matching the requested credential type."""

        allowed_types = [credential_type] if isinstance(credential_type, str) else credential_type
        if selected_id:
            credential = next(
                (
                    item
                    for item in self.credentials
                    if str(item.get("id")) == selected_id and item.get("type") in allowed_types
                ),
                None,
            )
            if credential:
                data = credential.get("data")
                return data if isinstance(data, dict) else None

        credential = next(
            (item for item in self.credentials if item.get("type") in allowed_types),
            None,
        )
        data = credential.get("data") if credential else None
        return data if isinstance(data, dict) else None
