"""
services/__init__.py
--------------------
Exposes common domain services for urban intelligence event processing.
"""

from app.services.bus_service import upsert_bus
from app.services.hotspot_service import process_event_for_hotspot
from app.services.event_aggregator import get_aggregator, EventAggregator
from app.services.ws_broadcaster import get_broadcaster, WSBroadcaster

__all__ = [
    "upsert_bus",
    "process_event_for_hotspot",
    "get_aggregator",
    "EventAggregator",
    "get_broadcaster",
    "WSBroadcaster",
]
