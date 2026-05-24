from typing import Any

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.registry.registry import node_registry

logger = get_logger(__name__)


class NodeExecutor:
    def _normalize_credential_types(self, credential_type: Any) -> list[str]:
        if isinstance(credential_type, str):
            return [credential_type]
        if isinstance(credential_type, list):
            return [item for item in credential_type if isinstance(item, str)]
        return []

    def _condition_matches(self, condition: Any, properties: dict[str, Any]) -> bool:
        if not isinstance(condition, dict):
            return True

        field = condition.get("field")
        expected = condition.get("value")
        if not isinstance(field, str):
            return True

        actual = properties.get(field)
        if isinstance(expected, list):
            return actual in expected
        return actual == expected

    def _credential_types_for_property(
        self,
        prop: dict[str, Any],
        properties: dict[str, Any],
    ) -> list[str]:
        static_type = prop.get("credentialType")
        if static_type:
            return self._normalize_credential_types(static_type)

        dynamic_config = prop.get("credentialTypeByField")
        if not isinstance(dynamic_config, dict):
            return []

        field_name = dynamic_config.get("field")
        values_map = dynamic_config.get("values")
        if not isinstance(field_name, str) or not isinstance(values_map, dict):
            return []

        field_value = properties.get(field_name)
        return self._normalize_credential_types(values_map.get(field_value))

    def _credential_spec(
        self,
        metadata_properties: list[dict[str, Any]],
        metadata_credential_type: Any,
        properties: dict[str, Any],
    ) -> tuple[list[str], str | None] | None:
        credential_props = [
            prop
            for prop in metadata_properties
            if prop.get("type") == "credential" and self._condition_matches(prop.get("condition"), properties)
        ]

        fallback_spec = None
        for prop in credential_props:
            credential_types = self._credential_types_for_property(prop, properties)
            if credential_types:
                selected_id = properties.get(prop.get("name", "credential"))
                if selected_id:
                    return credential_types, str(selected_id)
                if fallback_spec is None:
                    fallback_spec = (credential_types, None)

        if fallback_spec:
            return fallback_spec

        credential_types = self._normalize_credential_types(metadata_credential_type)
        if not credential_types:
            return None

        selected_id = None
        for prop in credential_props:
            prop_name = prop.get("name")
            if isinstance(prop_name, str) and properties.get(prop_name):
                selected_id = properties[prop_name]
                break

        if selected_id is None:
            selected_id = properties.get("credential")

        return credential_types, str(selected_id) if selected_id else None

    def _resolve_credential(
        self,
        metadata_properties: list[dict[str, Any]],
        metadata_credential_type: Any,
        properties: dict[str, Any],
        context: NodeContext,
    ) -> dict[str, Any] | None:
        spec = self._credential_spec(metadata_properties, metadata_credential_type, properties)
        if not spec:
            return None

        allowed_types, selected_cred_id = spec
        logger.info(
            "Resolving credential for allowed types %s. Selected ID: %s",
            allowed_types,
            selected_cred_id,
        )

        return context.get_credential_data(allowed_types, selected_cred_id)

    async def execute_node(
        self,
        node_type: str,
        node_id: str,
        properties: dict[str, Any],
        input_data: dict[str, Any],
        context: NodeContext,
    ) -> NodeResult:
        try:
            node_class = node_registry.get_node(node_type)
            metadata = node_class.get_metadata()

            # 1. Instantiate (Pydantic validation happens in __init__)
            node_instance = node_class(node_id=node_id, properties=properties)

            # 2. Credential injection
            found_cred = self._resolve_credential(
                metadata_properties=metadata.properties,
                metadata_credential_type=metadata.credential_type,
                properties=properties,
                context=context,
            )
            if found_cred:
                logger.info("Found credential data for node %s", node_id)
                node_instance.credential = found_cred

            logger.info(f"Executing node {node_id} of type {node_type}")
            result = await node_instance.execute(input_data, context)
            return result
        except Exception as e:
            # Handle Pydantic validation errors gracefully
            from pydantic import ValidationError

            if isinstance(e, ValidationError):
                errors = []
                for error in e.errors():
                    # Convert field path to human-readable property name
                    loc = error["loc"]
                    field = loc[-1] if loc else "unknown"  # last segment is the field name
                    raw_msg = error["msg"]
                    # Strip pydantic noise
                    msg = raw_msg.replace("Value error, ", "").replace("String should ", "").strip()
                    errors.append(f'"{field}" — {msg}')
                error_msg = "Missing or invalid fields: " + "; ".join(errors)
                logger.warning(f"Node {node_id} validation failed: {error_msg}")
                return NodeResult(success=False, error=error_msg, logs=[error_msg])

            logger.error(f"Error executing node {node_id}: {str(e)}", exc_info=True)
            return NodeResult(success=False, error=str(e), logs=[f"System Error: {str(e)}"])


node_executor = NodeExecutor()
