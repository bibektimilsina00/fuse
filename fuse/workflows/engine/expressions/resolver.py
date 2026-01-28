import logging
import json
from typing import Any, Dict, Optional, List
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger(__name__)

class ExpressionResolver:
    """
    Resolves expressions in node configurations and inputs.
    Uses Jinja2 syntax (e.g. {{ $node.Webhook.json.body }}) with a restricted sandbox.
    """
    
    def __init__(self, context: Dict[str, Any]):
        self.env = SandboxedEnvironment()
        self.context = context
        
    def resolve(self, value: Any) -> Any:
        """
        Recursively resolve expressions in the given value.
        
        Args:
            value: The value to resolve (string, dict, list, or primitive)
            
        Returns:
            Resolved value
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(v) for v in value]
        else:
            return value

    def _resolve_string(self, value: str) -> Any:
        """
        Resolve a single string value if it contains an expression.
        """
        if not value or not isinstance(value, str):
            return value
            
        # Optimization: Only fire up Jinja if it looks like a template
        if "{{" in value and "}}" in value:
            try:
                # Handle pure expression case: "{{ $var }}" -> return var (typed), not string
                # Jinja renders to string by default. We might want to keep types if the whole string is an expression.
                # Heuristic: if string is exactly trimmed to {{ ... }}, try native evaluation or type casting.
                # For now, standard Jinja rendering behavior (strings).
                
                # Check for single variable expression to preserve type
                # This is a basic heuristic; robust implementation requires AST parsing or jinja NativeEnvironment
                stripped = value.strip()
                if stripped.startswith("{{") and stripped.endswith("}}") and stripped.count("{{") == 1:
                    # Using NativeEnvironment logic would be better here, but requires newer Jinja2
                    # For now, let's use the standard render and see.
                    # Actually, for JSON objects in expressions, stringification is annoying.
                    # N8n/Airflow often return strings unless specifically coerced.
                    pass

                template = self.env.from_string(value)
                rendered = template.render(**self.context)
                
                # Attempt to restore type if it looks like JSON?
                # No, that's dangerous. Let's return strings for now as per Jinja standard.
                return rendered
            except Exception as e:
                # Log warning but return original value so workflow doesn't crash on syntax error
                # unless strict mode is enabled.
                logger.warning(f"Expression resolution failed for '{value}': {e}")
                return value
        
        return value
