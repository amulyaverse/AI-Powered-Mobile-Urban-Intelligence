"""
services/bus_service.py
-----------------------
Shared service for bus fleet tracking, location updates, and state persistence.
Used by both the REST ingestion endpoint (routers/events.py) and the
live camera WebSocket pipeline (routers/camera_ws.py).
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.bus import Bus

DENSITY_TO_TRAFFIC = {
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High",
    "CRITICAL": "High",
}


def upsert_bus(
    db: Session,
    bus_id: Optional[str],
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    density: Optional[str] = None,
) -> Optional[Bus]:
    """
    Auto-register a bus if it has not been seen before.
    Updates GPS coordinates, traffic level, status, and last_seen timestamp.
    """
    if not bus_id:
        return None

    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        bus = Bus(id=bus_id, route=None)
        db.add(bus)

    if lat is not None:
        bus.last_lat = lat
    if lng is not None:
        bus.last_lng = lng
    if density is not None:
        bus.last_traffic = DENSITY_TO_TRAFFIC.get(density, "Unknown")

    bus.last_seen = datetime.now(timezone.utc)
    bus.status = "Active"
    return bus
