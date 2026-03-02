"""In-process async event bus for decoupled inter-module communication.

Modules publish events (e.g. 'ingestion.event.normalized') and other modules
subscribe handlers. This keeps the ingestion→mapping→sonar pipeline loosely coupled.

Swap this for Redis Streams or RabbitMQ later without changing module code.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

Handler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


@dataclass
class EventBus:
    _subscribers: dict[str, list[Handler]] = field(default_factory=lambda: defaultdict(list))

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                asyncio.create_task(handler(payload))
            except Exception:
                logger.exception("Event handler failed for %s", event_type)


# Singleton event bus instance — imported by modules to publish/subscribe
event_bus = EventBus()
