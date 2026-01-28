"""
Simple smoke test for HTTP Request Node Plugin

Run with: uv run python fuse_backend/node_packages/official/http-request/tests/test_simple.py
"""

import asyncio
import sys
from pathlib import Path

# Import the execute function directly
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from execute import execute, validate


async def test_basic_get():
    """Test basic GET request"""
    print("🧪 Test 1: Basic GET request...")
    
    context = {
        "config": {
            "url": "https://httpbin.org/get",
            "method": "GET"
        },
        "inputs": {}
    }
    
    result = await execute(context)
    
    assert result["status"] == 200, f"Expected 200, got {result['status']}"
    assert "data" in result, "Missing 'data' in result"
    assert "headers" in result, "Missing 'headers' in result"
    
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ Got response data")


async def test_post_request():
    """Test POST request"""
    print("\n🧪 Test 2: POST request with JSON body...")
    
    context = {
        "config": {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "body": {"test": "value", "number": 42}
        },
        "inputs": {}
    }
    
    result = await execute(context)
    
    assert result["status"] == 200, f"Expected 200, got {result['status']}"
    assert "data" in result, "Missing 'data' in result"
    
    print(f"   ✅ Status: {result['status']}")
    print(f"   ✅ POST successful")


async def test_validation():
    """Test config validation"""
    print("\n🧪 Test 3: Configuration validation...")
    
    # Valid config
    valid_result = await validate({"url": "https://example.com", "method": "GET"})
    assert valid_result["valid"] is True, "Valid config marked as invalid"
    print("   ✅ Valid config passed")
    
    # Invalid config
    invalid_result = await validate({"method": "GET"})  # Missing URL
    assert invalid_result["valid"] is False, "Invalid config marked as valid"
    assert len(invalid_result["errors"]) > 0, "No errors reported"
    print(f"   ✅ Invalid config detected: {invalid_result['errors']}")


async def test_url_protocol():
    """Test automatic https:// addition"""
    print("\n🧪 Test 4: Auto-add https://...")
    
    context = {
        "config": {
            "url": "httpbin.org/get",  # No protocol
            "method": "GET"
        },
        "inputs": {}
    }
    
    result = await execute(context)
    assert result["status"] == 200, "Request with auto-added protocol failed"
    print("   ✅ Protocol auto-added successfully")


async def test_error_handling():
    """Test error handling"""
    print("\n🧪 Test 5: Error handling...")
    
    context = {
        "config": {
            "method": "GET"
            # Missing URL
        },
        "inputs": {}
    }
    
    try:
        await execute(context)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "URL is required" in str(e)
        print(f"   ✅ Error caught: {e}")


async def main():
    print("=" * 60)
    print("🔌 HTTP Request Node Plugin - Smoke Tests")
    print("=" * 60)
    
    tests = [
        test_basic_get,
        test_post_request,
        test_validation,
        test_url_protocol,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"   ❌ FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"✨ Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
