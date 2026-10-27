"""
Event broadcasting queue for Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, List, Set

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """
    In-memory publisher-subscriber hub for broadcasting SSE events to web clients.
    """

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """Subscribe a new client queue."""
        q = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        logger.debug("New SSE client subscribed. Total: %d", len(self._subscribers))
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Unsubscribe a client queue."""
        self._subscribers.discard(q)
        logger.debug("SSE client disconnected. Total: %d", len(self._subscribers))

    async def broadcast(self, event_type: str, data: Dict):
        """Broadcast an event payload to all subscribed clients."""
        if not self._subscribers:
            return

        payload = {
            "event": event_type,
            "data": json.dumps(data),
        }

        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead_queues.append(q)

        for dq in dead_queues:
            self.unsubscribe(dq)


# Global singleton instance
broadcaster = EventBroadcaster()
