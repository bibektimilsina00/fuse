"""
Feature flags system for gradual feature rollouts and A/B testing.

This module provides a simple but extensible feature flag system that supports:
- Boolean flags (on/off)
- Percentage rollouts
- User-based targeting
- Environment-based defaults

Usage:
    from src.utils.feature_flags import FeatureFlags, is_enabled

    # Check if feature is enabled
    if is_enabled("new_workflow_editor"):
        # Use new editor
        pass

    # Check with user context
    if FeatureFlags.is_enabled_for_user("beta_features", user_id="user-123"):
        # Show beta features
        pass
"""

import hashlib
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RolloutStrategy(Enum):
    """Feature rollout strategies."""

    ALL = "all"  # Enabled for everyone
    NONE = "none"  # Disabled for everyone
    PERCENTAGE = "percentage"  # Percentage-based rollout
    USER_LIST = "user_list"  # Specific user IDs
    ENVIRONMENT = "environment"  # Based on environment


@dataclass
class FeatureFlag:
    """Configuration for a single feature flag."""

    name: str
    description: str = ""
    enabled: bool = False
    strategy: RolloutStrategy = RolloutStrategy.ALL
    percentage: int = 0  # For percentage rollout (0-100)
    allowed_users: Set[str] = field(default_factory=set)
    allowed_environments: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default feature flags configuration
# These can be overridden via environment variables or database
DEFAULT_FLAGS: Dict[str, FeatureFlag] = {
    # Workflow features
    "workflow_v2_editor": FeatureFlag(
        name="workflow_v2_editor",
        description="Enable the new V2 workflow editor",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "ai_workflow_generation": FeatureFlag(
        name="ai_workflow_generation",
        description="Enable AI-powered workflow generation",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "code_execution_sandbox": FeatureFlag(
        name="code_execution_sandbox",
        description="Enable sandboxed code execution for workflows",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    # Security features
    "enhanced_rate_limiting": FeatureFlag(
        name="enhanced_rate_limiting",
        description="Enable enhanced rate limiting with Redis",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "request_id_tracing": FeatureFlag(
        name="request_id_tracing",
        description="Enable request ID tracing for debugging",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    # Experimental features
    "beta_features": FeatureFlag(
        name="beta_features",
        description="Enable beta features for testing",
        enabled=False,
        strategy=RolloutStrategy.USER_LIST,
        allowed_users=set(),
    ),
    "experimental_nodes": FeatureFlag(
        name="experimental_nodes",
        description="Enable experimental workflow nodes",
        enabled=False,
        strategy=RolloutStrategy.PERCENTAGE,
        percentage=10,  # 10% rollout
    ),
    # Performance features
    "response_caching": FeatureFlag(
        name="response_caching",
        description="Enable Redis response caching",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "circuit_breakers": FeatureFlag(
        name="circuit_breakers",
        description="Enable circuit breakers for external services",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    # Integration features
    "google_sheets_integration": FeatureFlag(
        name="google_sheets_integration",
        description="Enable Google Sheets workflow nodes",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "slack_integration": FeatureFlag(
        name="slack_integration",
        description="Enable Slack workflow nodes",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
    "discord_integration": FeatureFlag(
        name="discord_integration",
        description="Enable Discord workflow nodes",
        enabled=True,
        strategy=RolloutStrategy.ALL,
    ),
}


class FeatureFlags:
    """
    Feature flags manager with support for various rollout strategies.

    Flags can be configured via:
    1. DEFAULT_FLAGS dictionary (code defaults)
    2. Environment variables (FEATURE_FLAG_<NAME>=true/false)
    3. Runtime updates via set_flag method
    """

    _flags: Dict[str, FeatureFlag] = {}
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize feature flags from defaults and environment."""
        if cls._initialized:
            return

        # Start with default flags
        cls._flags = {name: flag for name, flag in DEFAULT_FLAGS.items()}

        # Override with environment variables
        for name, flag in cls._flags.items():
            env_key = f"FEATURE_FLAG_{name.upper()}"
            env_value = os.environ.get(env_key)

            if env_value is not None:
                flag.enabled = env_value.lower() in ("true", "1", "yes", "on")
                logger.debug(
                    f"Feature flag '{name}' set to {flag.enabled} from environment"
                )

        cls._initialized = True
        logger.info(f"Initialized {len(cls._flags)} feature flags")

    @classmethod
    def get_flag(cls, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        cls.initialize()
        return cls._flags.get(name)

    @classmethod
    def is_enabled(cls, name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            name: The feature flag name

        Returns:
            True if enabled, False otherwise
        """
        cls.initialize()
        flag = cls._flags.get(name)

        if flag is None:
            logger.warning(f"Unknown feature flag: {name}")
            return False

        if not flag.enabled:
            return False

        if flag.strategy == RolloutStrategy.ALL:
            return True
        elif flag.strategy == RolloutStrategy.NONE:
            return False
        elif flag.strategy == RolloutStrategy.ENVIRONMENT:
            current_env = os.environ.get("ENVIRONMENT", "development")
            return current_env in flag.allowed_environments

        # For user-specific strategies, default to enabled without context
        return flag.enabled

    @classmethod
    def is_enabled_for_user(cls, name: str, user_id: str) -> bool:
        """
        Check if a feature is enabled for a specific user.

        Args:
            name: The feature flag name
            user_id: The user's unique identifier

        Returns:
            True if enabled for this user, False otherwise
        """
        cls.initialize()
        flag = cls._flags.get(name)

        if flag is None:
            logger.warning(f"Unknown feature flag: {name}")
            return False

        if not flag.enabled:
            return False

        if flag.strategy == RolloutStrategy.ALL:
            return True
        elif flag.strategy == RolloutStrategy.NONE:
            return False
        elif flag.strategy == RolloutStrategy.USER_LIST:
            return user_id in flag.allowed_users
        elif flag.strategy == RolloutStrategy.PERCENTAGE:
            # Consistent hashing for percentage rollout
            hash_value = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
            return (hash_value % 100) < flag.percentage
        elif flag.strategy == RolloutStrategy.ENVIRONMENT:
            current_env = os.environ.get("ENVIRONMENT", "development")
            return current_env in flag.allowed_environments

        return flag.enabled

    @classmethod
    def set_flag(
        cls,
        name: str,
        enabled: bool,
        strategy: Optional[RolloutStrategy] = None,
        percentage: Optional[int] = None,
        allowed_users: Optional[Set[str]] = None,
    ) -> None:
        """
        Update a feature flag at runtime.

        Args:
            name: The feature flag name
            enabled: Whether the flag is enabled
            strategy: Optional new rollout strategy
            percentage: Optional new percentage (for percentage rollout)
            allowed_users: Optional new user whitelist
        """
        cls.initialize()

        if name not in cls._flags:
            # Create new flag
            cls._flags[name] = FeatureFlag(name=name, enabled=enabled)

        flag = cls._flags[name]
        flag.enabled = enabled

        if strategy is not None:
            flag.strategy = strategy
        if percentage is not None:
            flag.percentage = max(0, min(100, percentage))
        if allowed_users is not None:
            flag.allowed_users = allowed_users

        logger.info(f"Feature flag '{name}' updated: enabled={enabled}")

    @classmethod
    def add_user_to_flag(cls, name: str, user_id: str) -> bool:
        """Add a user to a feature flag's allowed users list."""
        cls.initialize()
        flag = cls._flags.get(name)

        if flag is None:
            return False

        flag.allowed_users.add(user_id)
        logger.info(f"Added user '{user_id}' to feature flag '{name}'")
        return True

    @classmethod
    def remove_user_from_flag(cls, name: str, user_id: str) -> bool:
        """Remove a user from a feature flag's allowed users list."""
        cls.initialize()
        flag = cls._flags.get(name)

        if flag is None:
            return False

        flag.allowed_users.discard(user_id)
        logger.info(f"Removed user '{user_id}' from feature flag '{name}'")
        return True

    @classmethod
    def get_all_flags(cls) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags with their current status."""
        cls.initialize()
        return {
            name: {
                "name": flag.name,
                "description": flag.description,
                "enabled": flag.enabled,
                "strategy": flag.strategy.value,
                "percentage": (
                    flag.percentage
                    if flag.strategy == RolloutStrategy.PERCENTAGE
                    else None
                ),
                "user_count": (
                    len(flag.allowed_users)
                    if flag.strategy == RolloutStrategy.USER_LIST
                    else None
                ),
            }
            for name, flag in cls._flags.items()
        }

    @classmethod
    def reset(cls) -> None:
        """Reset feature flags to defaults (useful for testing)."""
        cls._flags = {}
        cls._initialized = False
        cls.initialize()


# Convenience function
def is_enabled(name: str) -> bool:
    """Check if a feature flag is enabled."""
    return FeatureFlags.is_enabled(name)


def is_enabled_for_user(name: str, user_id: str) -> bool:
    """Check if a feature flag is enabled for a specific user."""
    return FeatureFlags.is_enabled_for_user(name, user_id)
