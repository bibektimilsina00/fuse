"""
Test the new Node Package System

Verifies that NodeRegistry can discover and execute packaged nodes.

Run: uv run python fuse_backend/tests/test_node_system.py
"""

import asyncio
import sys
from pathlib import Path

# Import NodeRegistry directly without triggering engine/__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "registry",
    Path(__file__).parent.parent / "fuse/workflows/engine/nodes/registry.py"
)
registry_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry_module)
NodeRegistry = registry_module.NodeRegistry


async def main():
    print("=" * 70)
    print("🧪 Node Package System Test")
    print("=" * 70)
    
    # Initialize registry
    print("\n📦 Initializing NodeRegistry...")
    NodeRegistry.initialize()
    
    # List all nodes
    nodes = NodeRegistry.list_nodes()
    print(f"\n✅ Discovered {len(nodes)} nodes:")
    
    for node_id, node_info in nodes.items():
        print(f"   • {node_info['name']} ({node_id}) - {node_info['category']}")
    
    # Test HTTP Request node
    if "http.request" in nodes:
        print("\n" + "=" * 70)
        print("🧪 Testing HTTP Request Node")
        print("=" * 70)
        
        config = {
            "url": "https://api.github.com/zen",
            "method": "GET"
        }
        
        print(f"\n📤 Making request to: {config['url']}")
        
        try:
            result = await NodeRegistry.execute_node(
                node_id="http.request",
                config=config,
                inputs={}
            )
            
            print(f"\n✅ Success!")
            print(f"   Status: {result.get('status')}")
            print(f"   Data: {str(result.get('data'))[:100]}...")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Get schemas (for AI system)
    print("\n" + "=" * 70)
    print("📋 Node Schemas (for AI)")
    print("=" * 70)
    
    schemas = NodeRegistry.get_all_schemas()
    print(f"\nGenerated {len(schemas)} schemas for AI system")
    
    for schema in schemas[:3]:  # Show first 3
        print(f"\n{schema['name']}:")
        print(f"  Type: {schema['type']}")
        print(f"  Category: {schema['category']}")
        print(f"  Inputs: {len(schema['inputs'])}")
        print(f"  Outputs: {len(schema['outputs'])}")
    
    print("\n" + "=" * 70)
    print("✨ Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
