"""
Credentials Management Module

Provides secure storage and retrieval of external service credentials
for use in workflow automation nodes.
"""

from .router import router
from .service import get_credential_by_id, resolve_secret

__all__ = ['router', 'get_credential_by_id', 'resolve_secret']
