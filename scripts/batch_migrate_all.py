"""
Batch Node Migration Script

Automatically converts all nodes from the old system to plugins.

Run: uv run python fuse_backend/scripts/batch_migrate_all.py
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# Node mapping: (source_file, plugin_name, category)
NODES_TO_MIGRATE: List[Tuple[str, str, str]] = [
    # Actions
    ("fuse/workflows/engine/nodes/actions/code.py", "code-executor", "utilities"),
    ("fuse/workflows/engine/nodes/actions/data.py", "data-transform", "utilities"),
    ("fuse/workflows/engine/nodes/actions/discord.py", "discord-send", "communication"),
    ("fuse/workflows/engine/nodes/actions/email.py", "email-send", "communication"),
    ("fuse/workflows/engine/nodes/actions/google_sheets.py", "google-sheets", "data"),
    ("fuse/workflows/engine/nodes/actions/slack.py", "slack-send", "communication"),
    ("fuse/workflows/engine/nodes/actions/utility.py", "utility", "utilities"),
    ("fuse/workflows/engine/nodes/actions/whatsapp.py", "whatsapp-send", "communication"),
    
    # Triggers
    ("fuse/workflows/engine/nodes/triggers/email.py", "email-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/form.py", "form-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/manual.py", "manual-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/rss.py", "rss-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/schedule.py", "schedule-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/webhook.py", "webhook-trigger", "triggers"),
    ("fuse/workflows/engine/nodes/triggers/whatsapp.py", "whatsapp-trigger", "triggers"),
    
    # Logic
    ("fuse/workflows/engine/nodes/logic/delay.py", "delay", "logic"),
    ("fuse/workflows/engine/nodes/logic/if_node.py", "if-condition", "logic"),
    ("fuse/workflows/engine/nodes/logic/loop.py", "loop", "logic"),
    ("fuse/workflows/engine/nodes/logic/merge.py", "merge", "logic"),
    ("fuse/workflows/engine/nodes/logic/parallel.py", "parallel", "logic"),
    ("fuse/workflows/engine/nodes/logic/pause.py", "pause", "logic"),
    ("fuse/workflows/engine/nodes/logic/switch.py", "switch", "logic"),
    
    # AI
    ("fuse/workflows/engine/nodes/ai/agent.py", "ai-agent", "ai"),
    ("fuse/workflows/engine/nodes/ai/chat_model.py", "ai-chat", "ai"),
    ("fuse/workflows/engine/nodes/ai/llm.py", "ai-llm", "ai"),
    ("fuse/workflows/engine/nodes/ai/memory.py", "ai-memory", "ai"),
    ("fuse/workflows/engine/nodes/ai/tool.py", "ai-tool", "ai"),
]


def create_plugin_scaffold(plugin_name: str, category: str, base_dir: Path):
    """Create the basic plugin structure"""
    plugin_dir = base_dir / plugin_name
    
    # Create directories
    (plugin_dir / "backend").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "frontend").mkdir(parents=True, exist_ok=True)
    (plugin_dir / "tests").mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = {
        "id": plugin_name.replace("-", "."),
        "name": plugin_name.replace("-", " ").title(),
        "version": "1.0.0",
        "author": "Fuse Official",
        "category": category,
        "description": f"{plugin_name.replace('-', ' ').title()} node",
        "tags": [category],
        "icon": get_icon_for_category(category),
        "runtime": {
            "type": "internal",
            "language": "python",
            "min PythonVersion": "3.9"
        },
        "inputs": [],
        "outputs": [],
        "credentials": None,
        "pricing": {"model": "free", "price": 0},
        "visibility": "public",
        "license": "MIT"
    }
    
    with open(plugin_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create execute.py template
    execute_template = '''"""
{} Plugin

TODO: Migrate logic from old node system
"""

from typing import Any, Dict


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the node.
    
    Args:
        context: Execution context with config, inputs, credentials
        
    Returns:
        Dict with outputs
    """
    config = context.get("config", {{}})
    inputs = context.get("inputs", {{}})
    
    # TODO: Implement node logic
    
    return {{}}


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration"""
    return {{"valid": True, "errors": []}}
'''.format(plugin_name.replace("-", " ").title())
    
    with open(plugin_dir / "backend" / "execute.py", "w") as f:
        f.write(execute_template)
    
    # Create requirements.txt
    (plugin_dir / "backend" / "requirements.txt").touch()
    
    # Create README
    readme = f"# {plugin_name.replace('-', ' ').title()}\n\nTODO: Add documentation\n"
    with open(plugin_dir / "README.md", "w") as f:
        f.write(readme)
    
    # Create test template
    test_template = '''"""
Tests for {} plugin
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from execute import execute, validate


async def test_basic():
    """Basic test"""
    context = {{
        "config": {{}},
        "inputs": {{}}
    }}
    
    result = await execute(context)
    print(f"✓ Result: {{result}}")


if __name__ == "__main__":
    asyncio.run(test_basic())
'''.format(plugin_name)
    
    with open(plugin_dir / "tests" / "test_simple.py", "w") as f:
        f.write(test_template)
    
    (plugin_dir / "tests" / "__init__.py").touch()
    
    return plugin_dir


def get_icon_for_category(category: str) -> str:
    """Map category to icon"""
    icons = {
        "communication": "message-circle",
        "data": "database",
        "utilities": "tool",
        "triggers": "zap",
        "logic": "git-branch",
        "ai": "cpu"
    }
    return icons.get(category, "cube")


def main():
    print("=" * 70)
    print("🚀 BATCH NODE MIGRATION")
    print("=" * 70)
    print(f"\nMigrating {len(NODES_TO_MIGRATE)} nodes to plugin system...")
    print()
    
    base_dir = Path("fuse_backend/node_packages/official")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    created = []
    skipped = []
    
    for source_file, plugin_name, category in NODES_TO_MIGRATE:
        # Skip http-request and email-send (already done)
        if plugin_name in ["http-request", "email-send"]:
            skipped.append((plugin_name, "already exists"))
            continue
        
        plugin_dir = base_dir / plugin_name
        
        # Skip if already exists
        if plugin_dir.exists():
            skipped.append((plugin_name, "directory exists"))
            continue
        
        try:
            created_dir = create_plugin_scaffold(plugin_name, category, base_dir)
            created.append(plugin_name)
            print(f"✓ Created: {plugin_name} ({category})")
        except Exception as e:
            print(f"✗ Failed: {plugin_name} - {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 SUMMARY")
    print("=" * 70)
    print(f"✅ Created: {len(created)} plugins")
    print(f"⏭️  Skipped: {len(skipped)} plugins")
    
    if created:
        print(f"\n📦 New Plugins:")
        for name in created:
            print(f"   • {name}")
    
    if skipped:
        print(f"\n⏭️  Skipped:")
        for name, reason in skipped:
            print(f"   • {name} ({reason})")
    
    print("\n" + "=" * 70)
    print("✨ Next Steps:")
    print("=" * 70)
    print("1. For each plugin, copy the execute() logic from the old node")
    print("2. Update manifest.json with proper inputs/outputs")
    print("3. Add dependencies to requirements.txt")
    print("4. Write tests in tests/test_simple.py")
    print("5. Update README.md with documentation")
    print("\nTIP: Focus on high-priority nodes first!")
    print("=" * 70)


if __name__ == "__main__":
    main()
