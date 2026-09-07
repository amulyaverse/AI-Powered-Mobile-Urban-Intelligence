"""
services/event_aggregator.py
-----------------------------
Temporal deduplication layer for the WebSocket camera pipeline.

The bus camera streams frames at 2 fps continuously. Without deduplication
every pothole or traffic snapshot would create a new DB row every 500 ms —
i.e., 120 rows per minute per bus per event type.

This aggregator suppresses events of the same type from the same bus within
a configurable time window (AGGREGATOR_SUPPRESS_WINDOW_SEC, default 10 s).

Override: if a new detection's confidence is significantly higher than the
cached one (by AGGREGATOR_CONF_OVERRIDE_DELTA), it is emitted immediately
regardless of the window, because a clearer/better image of the same object
is worth storing.

Thread-safe: uses threading.Lock so the WebSocket coroutine can call it
safely from an asyncio thread-pool executor.
"""

from __future__ import annotations

from threading import Lock
from time import monotonic

from app.config import get_settings

settings = get_settings()


class EventAggregator:
    """
    Tracks the last emission time and confidence per (bus_id, event_type) pair
    and decides whether a new detection should be persisted.
    """

    def __init__(self):
        # key: (bus_id, event_type) → (last_emit_monotonic, last_confidence)
        self._cache: dict[tuple[str, str], tuple[float, float]] = {}
        self._lock = Lock()

    def should_emit(self, bus_id: str, event_type: str, confidence: float) -> bool:
        """
        Return True if this detection should be persisted as a new event.

        A detection is emitted when:
          1. No prior event of this type from this bus exists in the cache.
          2. The suppress window has expired.
          3. The confidence improvement over the cached detection exceeds
             AGGREGATOR_CONF_OVERRIDE_DELTA (better shot of the same thing).
        """
        key = (bus_id, event_type)
        window = settings.AGGREGATOR_SUPPRESS_WINDOW_SEC
        delta_threshold = settings.AGGREGATOR_CONF_OVERRIDE_DELTA

        with self._lock:
            if key not in self._cache:
                return True

            last_time, last_conf = self._cache[key]
            age = monotonic() - last_time

            if age >= window:
                return True

            if confidence - last_conf >= delta_threshold:
                return True

            return False

    def record(self, bus_id: str, event_type: str, confidence: float) -> None:
        """Record that an event was just emitted for (bus_id, event_type)."""
        key = (bus_id, event_type)
        with self._lock:
            self._cache[key] = (monotonic(), confidence)

    def reset(self, bus_id: str | None = None) -> None:
        """
        Clear the cache for a specific bus (on disconnect) or entirely.
        Call with bus_id=None to clear everything (useful in tests).
        """
        with self._lock:
            if bus_id is None:
                self._cache.clear()
            else:
                keys_to_delete = [k for k in self._cache if k[0] == bus_id]
                for k in keys_to_delete:
                    del self._cache[k]


# ── Module-level singleton ────────────────────────────────────────────────────
_aggregator = EventAggregator()


def get_aggregator() -> EventAggregator:
    """Return the shared EventAggregator singleton."""
    return _aggregator
