"""
routers/events.py
-----------------
All event-related API endpoints.

POST /api/events         — ingest a new event from AI / integration layer
GET  /api/events         — list all events with optional filters
GET  /api/events/{id}    — single event by ID
PATCH /api/events/{id}/status — update event status
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.bus import Bus
from app.schemas.event import EventCreate, EventResponse, EventStatusUpdate
from app.services.hotspot_service import process_event_for_hotspot
from app.config import get_settings

router = APIRouter(prefix="/api/events", tags=["Events"])
settings = get_settings()


def _upsert_bus(db: Session, event_data: EventCreate) -> None:
    """
    Auto-register a bus if it has not been seen before.
    Updates GPS and traffic level on every event received.
    """
    if not event_data.bus_id:
        return

    bus = db.query(Bus).filter(Bus.id == event_data.bus_id).first()
    if not bus:
        bus = Bus(id=event_data.bus_id, route=None)
        db.add(bus)

    # Map density label to traffic level
    density_map = {"LOW": "Low", "MEDIUM": "Medium", "HIGH": "High", "CRITICAL": "High"}
    traffic = density_map.get(event_data.density or "", "Unknown")

    bus.last_lat = event_data.latitude
    bus.last_lng = event_data.longitude
    bus.last_traffic = traffic
    bus.last_seen = datetime.now(timezone.utc)
    bus.status = "Active"


@router.post("", response_model=EventResponse, status_code=201)
def ingest_event(payload: EventCreate, db: Session = Depends(get_db)):
    """
    Ingest a new event from the AI / integration layer.

    - Validates confidence threshold
    - Auto-registers or updates the reporting bus
    - Persists the event (preserving client-assigned event_id if provided)
    - Triggers hotspot clustering logic for road-damage events
    """
    # Reject low-confidence events
    if payload.confidence < settings.MIN_CONFIDENCE:
        raise HTTPException(
            status_code=422,
            detail=f"Confidence {payload.confidence:.2f} is below the minimum threshold of {settings.MIN_CONFIDENCE}.",
        )

    # Auto-register / update bus
    _upsert_bus(db, payload)
    db.flush()

    assigned_id = payload.event_id or f"EVT_{uuid.uuid4().hex[:8]}"
    assigned_status = payload.status or "new"

    # Persist the event
    event = Event(
        event_id=assigned_id,
        event_type=payload.event_type,
        confidence=payload.confidence,
        severity=payload.severity,
        bus_id=payload.bus_id,
        camera_id=payload.camera_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timestamp=payload.timestamp,
        evidence=payload.evidence,
        status=assigned_status,
        repeated_detections=1,
        # Traffic-specific fields
        car_count=payload.car_count,
        bike_count=payload.bike_count,
        bus_count=payload.bus_count,
        truck_count=payload.truck_count,
        total_vehicles=payload.total_vehicles,
        density=payload.density,
        density_score=payload.density_score,
        source_frame=payload.source_frame,
        frame_coverage_ratio=payload.frame_coverage_ratio,
    )
    db.add(event)
    db.flush()  # Assign event_id before hotspot logic

    # Run hotspot intelligence (commits internally)
    process_event_for_hotspot(db, event)

    db.refresh(event)
    return event


@router.get("", response_model=List[EventResponse])
def list_events(
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    severity: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    bus_id: Optional[str] = Query(default=None, description="Filter by bus ID"),
    search: Optional[str] = Query(default=None, description="Search by event_id, bus_id, or event_type"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    """
    Return a list of events with optional filters.
    Results are sorted newest-first.
    """
    q = db.query(Event)
    if event_type:
        q = q.filter(Event.event_type == event_type)
    if severity:
        q = q.filter(Event.severity == severity)
    if status:
        q = q.filter(Event.status == status)
    if bus_id:
        q = q.filter(Event.bus_id == bus_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        q = q.filter(
            Event.event_id.ilike(search_pattern)
            | Event.bus_id.ilike(search_pattern)
            | Event.event_type.ilike(search_pattern)
        )
    return q.order_by(Event.timestamp.desc()).offset(offset).limit(limit).all()



@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: str, db: Session = Depends(get_db)):
    """Return a single event by its ID."""
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/{event_id}/status", response_model=EventResponse)
def update_event_status(
    event_id: str,
    payload: EventStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update the status of an event.
    Powers the 'Update Status' buttons in the EventPage modal.
    """
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.status = payload.status
    db.commit()
    db.refresh(event)
    return event
