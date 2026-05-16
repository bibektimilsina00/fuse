import datetime
import json
from abc import ABC, abstractmethod
from typing import Any

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


class IEventEmitter(ABC):
    @abstractmethod
    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event."""
        pass


class RedisEventEmitter(IEventEmitter):
    def __init__(self, execution_id: str):
        self.execution_id = execution_id

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        try:
            from apps.api.app.core.redis import get_redis

            redis = await get_redis()
            channel = f"execution:{self.execution_id}"

            event = {
                "type": event_type,
                "execution_id": self.execution_id,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
                **data,
            }

            await redis.publish(channel, json.dumps(event))
        except Exception as e:
            logger.warning(f"Failed to publish execution event for {self.execution_id}: {e}")


class NullEventEmitter(IEventEmitter):
    """Fallback emitter that does nothing."""

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        pass
