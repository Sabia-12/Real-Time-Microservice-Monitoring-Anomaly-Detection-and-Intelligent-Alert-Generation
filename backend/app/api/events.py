"""Server-Sent Events (SSE) streaming endpoint."""

import asyncio
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from backend.app.events import broadcaster

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("")
async def stream_events(request: Request):
    """
    Server-Sent Events endpoint pushing real-time anomalies, alerts, and incidents to dashboard.
    """
    queue = broadcaster.subscribe()

    async def event_generator():
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": '{"status":"connected"}',
            }

            while True:
                # Disconnect if client closed connection
                if await request.is_disconnected():
                    break

                try:
                    # Wait for next event with a timeout for ping/heartbeat
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield {
                        "event": "ping",
                        "data": '{"ping": true}',
                    }

        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())
