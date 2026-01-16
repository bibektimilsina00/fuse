import httpx
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class HTTPRuntime:
    """Handles network requests for the workflow engine."""
    
    @staticmethod
    async def request(
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Performs an asynchronous HTTP request."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if method.upper() != "GET" else None,
                    params=params
                )
                
                try:
                    data = response.json()
                except (ValueError, TypeError):
                    data = response.text
                    
                return {
                    "status": response.status_code,
                    "data": data,
                    "headers": dict(response.headers)
                }
        except Exception as e:
            logger.error(f"HTTP runtime request failed: {e}")
            raise RuntimeError(f"Network request failed: {str(e)}")
