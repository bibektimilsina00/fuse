"""
Node Migration Helper Script

Automates the conversion of old-style nodes to the new plugin format.

Usage:
    uv run python fuse_backend/scripts/migrate_node.py <source_file> <plugin_name>
    
Example:
    uv run python fuse_backend/scripts/migrate_node.py \\
        fuse/workflows/engine/nodes/actions/email.py \\
        email-send
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def extract_node_info(source_file: Path) -> Dict[str, Any]:
    """Extract node information from old-style node file"""
    with open(source_file, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    info = {
        "class_name": None,
        "schema": {},
        "imports": [],
        "execute_code": None
    }
    
    # Find the node class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if any(base.id == 'BaseNode' if isinstance(base, ast.Name) else False 
                   for base in node.bases):
                info["class_name"] = node.name
                
                # Find schema property
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == 'schema':
                        # Extract schema details (simplified)
                        pass
                    elif isinstance(item, ast.AsyncFunctionDef) and item.name == 'execute':
                        # Store execute function
                        info["execute_code"] = ast.get_source_segment(content, item)
    
    # Extract imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                info["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and not node.module.startswith('fuse.workflows'):
                info["imports"].append(node.module)
    
    return info


def create_plugin_structure(plugin_name: str, plugin_dir: Path):
    """Create the plugin directory structure"""
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "backend").mkdir(exist_ok=True)
    (plugin_dir / "frontend").mkdir(exist_ok=True)
    (plugin_dir / "tests").mkdir(exist_ok=True)


def generate_manifest(node_info: Dict[str, Any], plugin_name: str, category: str) -> Dict[str, Any]:
    """Generate manifest.json from node info"""
    # This is a template - would need to be customized per node
    manifest = {
        "id": plugin_name.replace("-", "."),
        "name": plugin_name.replace("-", " ").title(),
        "version": "1.0.0",
        "author": "Fuse Official",
        "category": category,
        "description": f"{plugin_name.replace('-', ' ').title()} node",
        "tags": [],
        "icon": "cube",
        "runtime": {
            "type": "internal",
            "language": "python",
            "minPythonVersion": "3.9"
        },
        "inputs": [],
        "outputs": [],
        "credentials": None,
        "pricing": {
            "model": "free",
            "price": 0
        },
        "visibility": "public",
        "license": "MIT"
    }
    
    return manifest


def generate_execute_py(node_info: Dict[str, Any], imports: List[str]) -> str:
    """Generate execute.py from node info"""
    imports_str = "\n".join(f"import {imp}" for imp in imports if imp not in ['typing', 'Any', 'Dict'])
    
    # Template - needs customization
    code = f'''"""
{node_info.get("class_name", "Node")} Plugin

Migrated from old node system.
"""

{imports_str}
from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the node with the provided configuration.
    
    Args:
        context: Execution context containing:
            - config: Node configuration
            - inputs: Runtime input data
            - credentials: Credentials (if required)
            
    Returns:
        Dict with outputs
    """
    config = context.get("config", {{}})
    inputs = context.get("inputs", {{}})
    credentials = context.get("credentials")
    
    # TODO: Implement node logic here
    # (Copy from original execute() method)
    
    return {{}}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration before execution.
    
    Returns:
        Dict with 'valid' (bool) and optional 'errors' (list)
    """
    errors = []
    
    # TODO: Add validation logic
    
    return {{
        "valid": len(errors) == 0,
        "errors": errors
    }}
'''
    
    return code


def migrate_node(source_file: Path, plugin_name: str, category: str = "utilities"):
    """Main migration function"""
    print(f"🔄 Migrating: {source_file.name} → {plugin_name}")
    
    # Extract node info
    node_info = extract_node_info(source_file)
    print(f"   Found class: {node_info['class_name']}")
    
    # Create plugin structure
    plugin_dir = Path("fuse_backend/node_packages/official") / plugin_name
    create_plugin_structure(plugin_name, plugin_dir)
    print(f"   Created: {plugin_dir}")
    
    # Generate manifest
    manifest = generate_manifest(node_info, plugin_name, category)
    with open(plugin_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"   ✓ manifest.json")
    
    # Generate execute.py
    execute_code = generate_execute_py(node_info, node_info["imports"])
    with open(plugin_dir / "backend" / "execute.py", 'w') as f:
        f.write(execute_code)
    print(f"   ✓ backend/execute.py")
    
    # Create requirements.txt
    (plugin_dir / "backend" / "requirements.txt").touch()
    print(f"   ✓ backend/requirements.txt")
    
    # Create README.md
    readme = f"# {plugin_name.replace('-', ' ').title()}\n\nMigrated node plugin.\n"
    with open(plugin_dir / "README.md", 'w') as f:
        f.write(readme)
    print(f"   ✓ README.md")
    
    # Create test file
    test_code = '''"""
Tests for this plugin
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from execute import execute, validate


async def test_basic():
    """Basic test"""
    context = {
        "config": {},
        "inputs": {}
    }
    
    result = await execute(context)
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_basic())
'''
    
    with open(plugin_dir / "tests" / "test_simple.py", 'w') as f:
        f.write(test_code)
    print(f"   ✓ tests/test_simple.py")
    
    print(f"✅ Migration scaffold created!")
    print(f"   Next steps:")
    print(f"   1. Review and customize manifest.json")
    print(f"   2. Copy execute logic to backend/execute.py")
    print(f"   3. Add dependencies to requirements.txt")
    print(f"   4. Write tests")
    print(f"   5. Test with: uv run python {plugin_dir}/tests/test_simple.py")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: migrate_node.py <source_file> <plugin_name> [category]")
        sys.exit(1)
    
    source = Path(sys.argv[1])
    plugin = sys.argv[2]
    cat = sys.argv[3] if len(sys.argv) > 3 else "utilities"
    
    if not source.exists():
        print(f"Error: {source} not found")
        sys.exit(1)
    
    migrate_node(source, plugin, cat)
