"""
Tests for HTTP Request Node Plugin

Run with: uv run pytest node_packages/official/http-request/tests/
"""

import pytest
import sys
from pathlib import Path

# Import the execute function directly
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from execute import execute, validate


@pytest.mark.asyncio
async def test_http_get_request():
    """Test basic GET request"""
    context = {
        "config": {
            "url": "https://httpbin.org/get",
            "method": "GET",
            "headers": {"User-Agent": "Fuse-Test"}
        },
        "inputs": {}
    }
    
    result = await execute(context)
    
    assert result["status"] == 200
    assert "data" in result
    assert "headers" in result


@pytest.mark.asyncio
async def test_http_post_request():
    """Test POST request with JSON body"""
    context = {
        "config": {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": {"test": "data", "foo": "bar"}
        },
        "inputs": {}
    }
    
    result = await execute(context)
    
    assert result["status"] == 200
    assert "data" in result
    # httpbin echoes back the posted data
    assert "json" in result["data"]


@pytest.mark.asyncio
async def test_missing_url():
    """Test that missing URL raises error"""
    context = {
        "config": {
            "method": "GET"
        },
        "inputs": {}
    }
    
    with pytest.raises(ValueError, match="URL is required"):
        await execute(context)


@pytest.mark.asyncio
async def test_url_protocol_auto_added():
    """Test that https:// is added if missing"""
    context = {
        "config": {
            "url": "httpbin.org/get",
            "method": "GET"
        },
        "inputs": {}
    }
    
    # Should work even though we didn't specify https://
    result = await execute(context)
    assert result["status"] == 200


@pytest.mark.asyncio
async def test_validate_config():
    """Test configuration validation"""
    # Valid config
    valid_config = {
        "url": "https://example.com",
        "method": "GET"
    }
    result = await validate(valid_config)
    assert result["valid"] is True
    
    # Invalid config - missing URL
    invalid_config = {
        "method": "GET"
    }
    result = await validate(invalid_config)
    assert result["valid"] is False
    assert "URL is required" in result["errors"]
    
    # Invalid method
    invalid_method = {
        "url": "https://example.com",
        "method": "INVALID"
    }
    result = await validate(invalid_method)
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_timeout_handling():
    """Test request timeout"""
    # Use httpbin delay endpoint to test timeout
    context = {
        "config": {
            "url": "https://httpbin.org/delay/35",  # Delays for 35 seconds (beyond 30s timeout)
            "method": "GET"
        },
        "inputs": {}
    }
    
    with pytest.raises(RuntimeError, match="timed out"):
        await execute(context)
