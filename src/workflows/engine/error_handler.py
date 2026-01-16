"""
Graceful Error Handling for Workflow Execution

Implements:
- Error classification (retryable vs permanent)
- Retry logic with exponential backoff
- Error policy enforcement (stop/continue/retry)
- Structured error context
"""

import logging
import asyncio
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Classification of errors for handling decisions."""
    CREDENTIAL_MISSING = "credential_missing"
    CREDENTIAL_INVALID = "credential_invalid"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    PERMISSION_DENIED = "permission_denied"
    CONFIGURATION_ERROR = "configuration_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Structured error information for logging and decisions."""
    category: ErrorCategory
    message: str
    original_error: str
    is_retryable: bool
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "message": self.message,
            "original_error": self.original_error,
            "is_retryable": self.is_retryable,
            "suggestion": self.suggestion
        }


class ErrorClassifier:
    """Classifies errors and determines handling strategy."""
    
    # Patterns for error classification
    PATTERNS = {
        ErrorCategory.CREDENTIAL_MISSING: [
            "credential", "not found", "missing credential", "no credential"
        ],
        ErrorCategory.CREDENTIAL_INVALID: [
            "invalid credential", "unauthorized", "authentication failed", 
            "invalid_grant", "token expired", "access denied", "invalid_auth", "invalid_token"
        ],
        ErrorCategory.RATE_LIMITED: [
            "rate limit", "too many requests", "429", "quota exceeded"
        ],
        ErrorCategory.NETWORK_ERROR: [
            "connection refused", "connection reset", "network unreachable",
            "dns", "ssl", "certificate"
        ],
        ErrorCategory.TIMEOUT: [
            "timeout", "timed out", "deadline exceeded"
        ],
        ErrorCategory.VALIDATION_ERROR: [
            "validation", "invalid input", "required field", "type error"
        ],
        ErrorCategory.RESOURCE_NOT_FOUND: [
            "not found", "404", "does not exist", "no such", "channel_not_found"
        ],
        ErrorCategory.PERMISSION_DENIED: [
            "permission denied", "forbidden", "403", "not allowed", "not_in_channel", "missing_scope", "invite it"
        ],
        ErrorCategory.CONFIGURATION_ERROR: [
            "configuration", "config error", "missing config", "invalid config", "required field", "channel id is required"
        ],
        ErrorCategory.EXTERNAL_SERVICE_ERROR: [
            "500", "502", "503", "504", "internal server error", "service unavailable",
            "slack api error", "openrouter", "openai error", "google api error", "model not found", "no endpoints found",
            "js execution error", "syntax error", "error executing code node"
        ]
    }
    
    # Categories that are safe to retry
    RETRYABLE_CATEGORIES = {
        ErrorCategory.RATE_LIMITED,
        ErrorCategory.NETWORK_ERROR,
        ErrorCategory.TIMEOUT,
        ErrorCategory.EXTERNAL_SERVICE_ERROR
    }
    
    # User-friendly suggestions per category
    SUGGESTIONS = {
        ErrorCategory.CREDENTIAL_MISSING: "Configure the required credential in the node settings.",
        ErrorCategory.CREDENTIAL_INVALID: "Re-authenticate or update your credential.",
        ErrorCategory.RATE_LIMITED: "Wait a moment and try again, or reduce request frequency.",
        ErrorCategory.NETWORK_ERROR: "Check your network connection and try again.",
        ErrorCategory.TIMEOUT: "The operation took too long. Try with smaller data or increase timeout.",
        ErrorCategory.VALIDATION_ERROR: "Check your input data matches the expected format.",
        ErrorCategory.RESOURCE_NOT_FOUND: "Verify the resource ID or URL is correct.",
        ErrorCategory.PERMISSION_DENIED: "Check your account has permission to access this resource, or ensure the bot/app has been invited and granted the necessary scopes.",
        ErrorCategory.CONFIGURATION_ERROR: "Review and fix the node configuration.",
        ErrorCategory.EXTERNAL_SERVICE_ERROR: "The external service is having issues. Try again later.",
        ErrorCategory.UNKNOWN: "An unexpected error occurred. Check the logs for details."
    }
    
    @classmethod
    def classify(cls, error: Exception) -> ErrorContext:
        """Classify an error and return structured context."""
        error_str = str(error).lower()
        original_error = str(error)
        
        # Find matching category
        matched_category = ErrorCategory.UNKNOWN
        for category, patterns in cls.PATTERNS.items():
            if any(pattern in error_str for pattern in patterns):
                matched_category = category
                break
        
        # Determine if retryable
        is_retryable = matched_category in cls.RETRYABLE_CATEGORIES
        
        # Get user-friendly message
        friendly_message = cls._get_friendly_message(matched_category, original_error)
        
        return ErrorContext(
            category=matched_category,
            message=friendly_message,
            original_error=original_error,
            is_retryable=is_retryable,
            suggestion=cls.SUGGESTIONS.get(matched_category)
        )
    
    @classmethod
    def _get_friendly_message(cls, category: ErrorCategory, original: str) -> str:
        """Generate a user-friendly error message."""
        # If the original error message is already descriptive (contains our custom prefix), use it
        lower_orig = original.lower()
        if "slack api error" in lower_orig or "ai model error" in lower_orig or "validation failed" in lower_orig:
            # Strip prefixes if they are too technical? No, keep them for clarity.
            return original

        messages = {
            ErrorCategory.CREDENTIAL_MISSING: "Credential not configured",
            ErrorCategory.CREDENTIAL_INVALID: "Credential is invalid or expired",
            ErrorCategory.RATE_LIMITED: "Rate limit exceeded",
            ErrorCategory.NETWORK_ERROR: "Network connection failed",
            ErrorCategory.TIMEOUT: "Operation timed out",
            ErrorCategory.VALIDATION_ERROR: "Input validation failed",
            ErrorCategory.RESOURCE_NOT_FOUND: "Resource not found",
            ErrorCategory.PERMISSION_DENIED: "Access Denied / Insufficient Permissions",
            ErrorCategory.CONFIGURATION_ERROR: "Invalid configuration",
            ErrorCategory.EXTERNAL_SERVICE_ERROR: "External service error",
            ErrorCategory.UNKNOWN: "Unexpected error"
        }
        return messages.get(category, "Error occurred")


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 30.0  # seconds
    
    @classmethod
    async def execute_with_retry(
        cls,
        func,
        *args,
        max_retries: int = None,
        base_delay: float = None,
        max_delay: float = None,
        **kwargs
    ) -> Tuple[Any, int]:
        """
        Execute a function with retry logic.
        Returns: (result, attempts_made)
        Raises: Last exception if all retries fail
        """
        max_retries = max_retries or cls.DEFAULT_MAX_RETRIES
        base_delay = base_delay or cls.DEFAULT_BASE_DELAY
        max_delay = max_delay or cls.DEFAULT_MAX_DELAY
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result, attempt + 1
            except Exception as e:
                last_error = e
                error_context = ErrorClassifier.classify(e)
                
                if not error_context.is_retryable:
                    logger.info(f"Error is not retryable ({error_context.category}): {e}")
                    raise
                
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed: {e}")
        
        raise last_error


class ErrorPolicyHandler:
    """Handles error policies at the node and workflow level."""
    
    @staticmethod
    def should_continue_workflow(
        error_context: ErrorContext,
        node_error_policy: str,
        workflow_error_policy: str = "stop"
    ) -> bool:
        """
        Determine if workflow should continue after a node error.
        
        Args:
            error_context: Classified error information
            node_error_policy: Node's error_policy setting
            workflow_error_policy: Workflow's default error policy
            
        Returns:
            True if workflow should continue, False to stop
        """
        # Node-level policy takes precedence
        policy = node_error_policy or workflow_error_policy
        
        if policy == "continue":
            return True
        elif policy == "stop":
            return False
        elif policy == "retry":
            # If we got here, retries already exhausted
            return False
        
        return False
    
    @staticmethod
    def get_fallback_output(error_context: ErrorContext) -> Dict[str, Any]:
        """Generate a fallback output for nodes with 'continue' error policy."""
        return {
            "_error": True,
            "_error_category": error_context.category.value,
            "_error_message": error_context.message,
            "_error_suggestion": error_context.suggestion,
            # Provide empty but structured output
            "data": None,
            "status": "error"
        }
