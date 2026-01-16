from typing import Any, Dict, Union
from jinja2 import Environment, BaseLoader, TemplateError, Undefined

# Custom loader that doesn't load from file system
class DictLoader(BaseLoader):
    def get_source(self, environment, template):
        return template, None, lambda: True

# Create a secure environment
# StrictUndefined raises an error if a variable doesn't exist, which is good for debugging
env = Environment(loader=DictLoader(), autoescape=True)

def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """
    Render a Jinja2 template string with the provided context.
    If the input is not a string, return it as is.
    """
    if not isinstance(template_str, str):
        return template_str
    
    # Optimization: if no template markers, return as is
    if "{{" not in template_str and "{%" not in template_str:
        return template_str

    try:
        template = env.from_string(template_str)
        return template.render(**context)
    except Exception as e:
        # In case of error (e.g. variable not found), we might want to fail or just return the original string
        # For now, let's treat it as a hard error if it's clearly a template
        # But for robustness, we can return the original string with a warning log?
        # Actually, if the user expects substitution and it fails, it's better to error out or return empty?
        # Let's raise an error so the node fails visibly.
        raise ValueError(f"Failed to render template '{template_str}': {str(e)}")

def render_values(data: Any, context: Dict[str, Any]) -> Any:
    """
    Recursively render templates in a dictionary or list.
    """
    if isinstance(data, str):
        return render_template(data, context)
    elif isinstance(data, dict):
        return {k: render_values(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [render_values(item, context) for item in data]
    else:
        return data
