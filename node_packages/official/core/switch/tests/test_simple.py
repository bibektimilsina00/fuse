"""
Tests for switch plugin
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
    print(f"✓ Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_basic())
