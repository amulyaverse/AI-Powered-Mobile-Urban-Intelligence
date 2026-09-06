"""
services/ws_broadcaster.py
---------------------------
In-process WebSocket pub/sub broadcaster.

All dashboard clients that subscribe to WS /api/ws/events are held in
this module-level singleton. When a camera stream produces a new event,
camera_ws.py calls broadcaster.broadcast(payload) and the payload is
immediately pushed to every connected dashboard client.

No Redis, no external message queue — works for a single-process Uvicorn
instance which is appropriate for the current deployment scale.
"""

from __future__ import annotations

import asyncio
from fastapi import WebSocket


class WSBroadcaster:
    """
    Manages a set of active WebSocket subscriber connections and provides
    a thread-safe broadcast method.
    """

    def __init__(self):
        self._subscribers: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._main_loop: asyncio.AbstractEventLoop | None = None

    async def subscribe(self, ws: WebSocket) -> None:
        """Register a new subscriber."""
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        async with self._lock:
            self._subscribers.add(ws)

    async def unsubscribe(self, ws: WebSocket) -> None:
        """Remove a subscriber (called on disconnect)."""
        async with self._lock:
            self._subscribers.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        """
        Push payload JSON to every subscriber.
        Dead connections (any send exception) are silently removed.
        """
        dead: set[WebSocket] = set()

        # Snapshot the set so we don't hold the lock during I/O
        async with self._lock:
            subscribers = set(self._subscribers)

        for ws in subscribers:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)

        if dead:
            async with self._lock:
                self._subscribers -= dead

    def broadcast_sync(self, payload: dict) -> None:
        """
        Broadcast payload JSON from a synchronous function or background thread.
        Schedules broadcast on the main event loop thread-safely.
        """
        if self._main_loop and self._main_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self._main_loop)
        else:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast(payload))
            except RuntimeError:
                try:
                    asyncio.run(self.broadcast(payload))
                except Exception as err:
                    print(f"[WSBroadcaster] broadcast_sync fallback error: {err}")

    @property
    def subscriber_count(self) -> int:
        """Number of currently connected dashboard clients."""
        return len(self._subscribers)


# ── Module-level singleton ────────────────────────────────────────────────────
_broadcaster = WSBroadcaster()


def get_broadcaster() -> WSBroadcaster:
    """Return the shared WSBroadcaster singleton."""
    return _broadcaster
