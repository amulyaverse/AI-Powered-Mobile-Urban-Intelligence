"""
services/hotspot_service.py
---------------------------
Persistent-detection intelligence layer.

On every road-damage event (pothole, road_defect), this service:
  1. Checks for existing events within HOTSPOT_RADIUS_METRES
  2. If found: increments repeated_detections and links to the existing hotspot
  3. If not found: creates a new hotspot record
  4. Escalates severity when detection_count reaches thresholds
  5. Auto-generates a SystemAlert when HOTSPOT_ALERT_THRESHOLD is crossed

The Haversine formula is used to compute the great-circle distance
between GPS coordinates — accurate enough for the ~50 m matching radius.
"""

from __future__ import annotations
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.config import get_settings

settings = get_settings()

# Event types that trigger hotspot matching
ROAD_DAMAGE_TYPES = {"pothole", "road_defect"}

# Severity escalation rules based on detection count
def _escalate_severity(count: int, base_severity: str) -> str:
    """Escalate severity as more buses confirm the same location."""
    if count >= 6:
        return "critical"
    if count >= 4:
        return "high"
    if count >= 2:
        return "medium"
    return base_severity


# Priority score weights per severity level
SEVERITY_WEIGHTS = {"low": 1.0, "medium": 2.0, "high": 3.5, "critical": 5.0}


def _haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the distance in metres between two GPS coordinates.
    Uses the Haversine formula.
    """
    R = 6_371_000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def process_event_for_hotspot(db: Session, new_event: Event) -> None:
    """
    Called immediately after a new Event is persisted.

    Only processes road-damage event types (pothole, road_defect).
    Traffic and congestion events do not feed the hotspot system.
    """
    if new_event.event_type not in ROAD_DAMAGE_TYPES:
        return

    radius = settings.HOTSPOT_RADIUS_METRES
    threshold = settings.HOTSPOT_ALERT_THRESHOLD

    # ── Find the nearest active hotspot within radius ─────────────────────────
    nearby_hotspot = _find_nearby_hotspot(db, new_event.latitude, new_event.longitude, radius)

    if nearby_hotspot:
        # Existing hotspot found — update it
        nearby_hotspot.detection_count += 1
        nearby_hotspot.last_seen = datetime.now(timezone.utc)

        # Update centroid to the average of all contributing events
        nearby_hotspot.center_lat = (nearby_hotspot.center_lat + new_event.latitude) / 2
        nearby_hotspot.center_lng = (nearby_hotspot.center_lng + new_event.longitude) / 2

        # Escalate severity
        nearby_hotspot.severity = _escalate_severity(nearby_hotspot.detection_count, new_event.severity)

        # Recalculate priority score
        nearby_hotspot.priority_score = _compute_priority(
            count=nearby_hotspot.detection_count,
            avg_confidence=new_event.confidence,
            severity=nearby_hotspot.severity,
        )

        # Link the new event to this hotspot
        new_event.hotspot_id = nearby_hotspot.id
        new_event.repeated_detections = nearby_hotspot.detection_count

        # Also update all previously linked events to reflect current count
        db.query(Event).filter(Event.hotspot_id == nearby_hotspot.id).update(
            {"repeated_detections": nearby_hotspot.detection_count},
            synchronize_session=False,
        )

        # Auto-generate a system alert when threshold is first crossed
        if nearby_hotspot.detection_count == threshold:
            _create_alert(
                db=db,
                severity="high" if nearby_hotspot.severity in ("low", "medium") else nearby_hotspot.severity,
                message=f"Persistent {new_event.event_type.replace('_', ' ')} detected — {threshold} independent reports",
                source=f"{threshold} buses observed",
                details=f"Location: {nearby_hotspot.center_lat:.4f}, {nearby_hotspot.center_lng:.4f}",
            )

    else:
        # No nearby hotspot — create a new one
        hotspot = Hotspot(
            center_lat=new_event.latitude,
            center_lng=new_event.longitude,
            event_type=new_event.event_type,
            detection_count=1,
            severity=new_event.severity,
            priority_score=_compute_priority(1, new_event.confidence, new_event.severity),
        )
        db.add(hotspot)
        db.flush()  # Get the new hotspot.id without committing

        new_event.hotspot_id = hotspot.id

    db.commit()


def _find_nearby_hotspot(
    db: Session, lat: float, lng: float, radius_m: float
) -> Optional[Hotspot]:
    """
    Return the nearest active hotspot within radius_m metres, or None.

    For SQLite/small datasets a Python-side distance check is fine.
    For production PostgreSQL, this can be upgraded to a PostGIS ST_DWithin query.
    """
    active_hotspots = db.query(Hotspot).filter(Hotspot.status == "active").all()
    closest: Optional[Hotspot] = None
    min_dist = float("inf")

    for h in active_hotspots:
        dist = _haversine_metres(lat, lng, h.center_lat, h.center_lng)
        if dist <= radius_m and dist < min_dist:
            min_dist = dist
            closest = h

    return closest


def _compute_priority(count: int, avg_confidence: float, severity: str) -> float:
    """priority_score = count × avg_confidence × severity_weight"""
    weight = SEVERITY_WEIGHTS.get(severity, 1.0)
    return round(count * avg_confidence * weight, 3)


def _create_alert(db: Session, severity: str, message: str, source: str, details: str) -> None:
    """Insert a new SystemAlert row."""
    alert = SystemAlert(
        id=str(uuid.uuid4()),
        severity=severity,
        message=message,
        source=source,
        details=details,
    )
    db.add(alert)
    # Don't commit here — caller controls the transaction
