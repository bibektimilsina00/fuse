import json
import re
from typing import Any

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

# Matches {{node_id.output.field}} or {{node_id.output.nested.field}}
TEMPLATE_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


class TemplateResolver:
    """Resolves {{node_id.output.field}} templates against execution context."""

    def __init__(self, node_outputs: dict[str, dict[str, Any]], trigger_data: dict[str, Any], variables: dict[str, Any]):
        # context: { "trigger": {"output": {...}}, "node_1": {"output": {...}}, "variables": {...} }
        self._context = {
            "trigger": {"output": trigger_data},
            "variables": variables,
            **{node_id: {"output": output} for node_id, output in node_outputs.items()},
        }

    def resolve_properties(self, properties: dict[str, Any]) -> dict[str, Any]:
        """Resolve all template strings in a node's properties dict recursively."""
        return self._resolve_recursive(properties)

    def _resolve_recursive(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self._resolve_recursive(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_recursive(item) for item in value]
        return value

    def _resolve_string(self, template: str) -> Any:
        matches = TEMPLATE_PATTERN.findall(template)
        if not matches:
            return template

        # If the entire string is exactly one template "{{path}}", preserve the resolved type
        # (e.g. if it resolves to a number, return a number, not a string "42")
        if len(matches) == 1 and template.strip() == f"{{{{{matches[0]}}}}}":
            return self._resolve_path(matches[0].strip())

        # If it's a mix of text and templates, always return a string
        def replace_match(match: re.Match) -> str:
            path = match.group(1).strip()
            resolved = self._resolve_path(path)
            if resolved is None:
                return ""
            if isinstance(resolved, (dict, list)):
                return json.dumps(resolved)
            return str(resolved)

        return TEMPLATE_PATTERN.sub(replace_match, template)

    def _resolve_path(self, path: str) -> Any:
        """Resolve a dot-path like 'node_1.output.body.id'."""
        parts = path.split(".")
        current = self._context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    logger.warning(f"Could not resolve index '{part}' in path '{path}'")
                    return None
            else:
                logger.warning(f"Could not resolve part '{part}' in path '{path}'")
                return None

            if current is None:
                return None

        return current
