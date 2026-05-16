from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine.node_executor import node_executor
from apps.api.app.node_system.base.node_context import NodeContext

logger = get_logger(__name__)


class WorkflowRunner:
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        graph: dict[str, Any],
        db: AsyncSession | None = None,
        on_log: Any = None,
        credentials: list[dict[str, Any]] | None = None,
        emitter: Any = None,  # Avoid circular import by using Any or string ref
    ):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph.get("nodes", [])}
        self.edges = graph.get("edges", [])
        self.executed_nodes: dict[str, Any] = {}
        self.node_outputs: dict[str, dict[str, Any]] = {}
        self.trigger_data: dict[str, Any] = {}
        self.credentials = credentials or []
        self.db = db
        self.on_log = on_log
        self.emitter = emitter
        self.variables: dict[str, Any] = {}
        self.failed = False
        self.error_message = None

    async def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Helper to emit execution events via the injected emitter."""
        if self.emitter:
            await self.emitter.emit(event_type, data)

    async def _log(
        self, message: str, level: str = "info", node_id: str | None = None, payload: Any = None
    ):
        if self.on_log:
            await self.on_log(message, level=level, node_id=node_id, payload=payload)

    async def run(self, trigger_data: dict[str, Any]) -> dict:
        self.trigger_data = trigger_data
        logger.info(f"Starting workflow execution {self.execution_id}")

        # 1. Find start nodes (nodes with no incoming edges)
        start_nodes = self._get_start_nodes()

        if not start_nodes:
            logger.info(f"Workflow {self.workflow_id} has no nodes — completing immediately")
            return {}

        for node_id in start_nodes:
            await self._execute_node_recursive(node_id, trigger_data)
            if self.failed:
                break

        if self.failed:
            raise Exception(self.error_message or "Execution failed")

        # Return output of last executed nodes
        if self.node_outputs:
            last_node_id = list(self.node_outputs.keys())[-1]
            return self.node_outputs[last_node_id]
        return {}

    def _get_start_nodes(self) -> list[str]:
        target_nodes = {edge["target"] for edge in self.edges}
        return [node_id for node_id in self.nodes if node_id not in target_nodes]

    async def _execute_node_recursive(self, node_id: str, input_data: dict[str, Any]):
        if node_id in self.executed_nodes or self.failed:
            return

        node_data = self.nodes[node_id]
        label = node_data.get("data", {}).get("label") or node_data["type"]

        await self._log(label, node_id=node_id)

        # Resolve templates in properties BEFORE executing
        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        resolver = TemplateResolver(
            node_outputs=self.node_outputs,
            trigger_data=self.trigger_data,
            variables=self.variables,
        )
        raw_properties = node_data.get("data", {}).get("properties", {})
        resolved_properties = resolver.resolve_properties(raw_properties)

        from apps.api.app.core.http import get_http_client

        http_client = await get_http_client()

        context = NodeContext(
            execution_id=self.execution_id,
            workflow_id=self.workflow_id,
            node_id=node_id,
            variables=self.variables,  # Use persistent state
            credentials=self.credentials,
            http_client=http_client,
            db=self.db,
        )

        # Emit NODE_STARTED
        await self._emit(
            "node_started", {"node_id": node_id, "node_type": node_data.get("type"), "label": label}
        )

        result = await node_executor.execute_node(
            node_type=node_data["type"],
            node_id=node_id,
            properties=resolved_properties,  # Pass resolved properties
            input_data=input_data,
            context=context,
        )

        self.executed_nodes[node_id] = result

        # Log individual node logs if any
        for log_msg in result.logs:
            await self._log(log_msg, level="info" if result.success else "error", node_id=node_id)

        next_edges = [edge for edge in self.edges if edge["source"] == node_id]

        if result.success:
            # Store output for future interpolation
            self.node_outputs[node_id] = result.output_data

            # Emit NODE_COMPLETED
            await self._emit(
                "node_completed",
                {
                    "node_id": node_id,
                    "output": result.output_data,
                },
            )

            await self._log(
                label,
                node_id=node_id,
                payload={
                    "input": resolved_properties,
                    "data_in": input_data,
                    "output": result.output_data,
                },
            )

            branch = result.output_data.get("branch")
            for edge in next_edges:
                edge_handle = edge.get("sourceHandle")

                # SKIP error branches on success
                if edge_handle == "error":
                    continue

                # Handle specific logical branches (e.g. from Condition node)
                if branch and edge_handle and edge_handle != branch:
                    continue

                await self._execute_node_recursive(edge["target"], result.output_data)
        else:
            # Handle Failure
            error_payload = {
                "input": resolved_properties,
                "data_in": input_data,
                "error": result.error,
            }

            # Emit NODE_FAILED
            await self._emit(
                "node_failed",
                {
                    "node_id": node_id,
                    "error": result.error,
                },
            )

            await self._log(
                label,
                level="error",
                node_id=node_id,
                payload=error_payload,
            )

            # Check if we have an error handler branch
            error_edges = [e for e in next_edges if e.get("sourceHandle") == "error"]

            if error_edges:
                logger.info(f"Node {node_id} failed, following {len(error_edges)} error branch(es)")
                for edge in error_edges:
                    await self._execute_node_recursive(edge["target"], error_payload)
            else:
                # No error handler -> workflow fails
                self.failed = True
                error = result.error or "Unknown error"
                self.error_message = error if "Node" in error else f"Node {label} failed: {error}"
                logger.error(f"Execution failed at node {node_id}: {result.error}")
