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
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.event import Event
from app.models.bus import Bus
from app.schemas.event import EventCreate, EventResponse, EventStatusUpdate
from app.services.hotspot_service import process_event_for_hotspot
from app.services.bus_service import upsert_bus
from app.config import get_settings

router = APIRouter(prefix="/api/events", tags=["Events"])
settings = get_settings()





@router.post("", response_model=EventResponse, status_code=201)
async def ingest_event(payload: EventCreate, db: Session = Depends(get_db)):
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

    event_lat = payload.latitude
    event_lng = payload.longitude

    # Enforce vicinity constraint for target bus
    if payload.bus_id == settings.TARGET_BUS_ID:
        from app.services.bus_location_service import haversine_distance_km, get_vicinity_coordinates
        existing_bus = db.query(Bus).filter(Bus.id == payload.bus_id).first()
        if existing_bus and existing_bus.last_lat is not None and existing_bus.last_lng is not None:
            dist = haversine_distance_km(existing_bus.last_lat, existing_bus.last_lng, event_lat, event_lng)
            if dist > settings.BUS_VICINITY_RADIUS_KM:
                event_lat, event_lng = get_vicinity_coordinates(
                    existing_bus.last_lat, existing_bus.last_lng, max_radius_km=settings.BUS_VICINITY_RADIUS_KM
                )

    # Auto-register / update bus
    upsert_bus(db, bus_id=payload.bus_id, lat=event_lat, lng=event_lng, density=payload.density)
    db.flush()

    assigned_id = payload.event_id or f"EVT_{uuid.uuid4().hex[:8]}"
    assigned_status = payload.status or "new"

    evidence_val = payload.evidence
    if evidence_val:
        ev_str = str(evidence_val).strip()
        try:
            local_file = Path(ev_str)
            if local_file.is_file() and local_file.exists():
                settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
                dest_filename = f"{assigned_id}.jpg"
                dest_path = settings.EVIDENCE_DIR / dest_filename
                shutil.copyfile(local_file, dest_path)
                evidence_val = f"/evidence/{dest_filename}"
        except Exception:
            pass

    # Persist the event
    event = Event(
        event_id=assigned_id,
        event_type=payload.event_type,
        confidence=payload.confidence,
        severity=payload.severity,
        bus_id=payload.bus_id,
        camera_id=payload.camera_id,
        latitude=event_lat,
        longitude=event_lng,
        timestamp=payload.timestamp,
        evidence=evidence_val,
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
        # PR 37 & 40 road defect fields
        bbox=payload.bbox,
        width_ratio=payload.width_ratio,
        area_ratio=payload.area_ratio,
        severity_method=payload.severity_method,
        surface_condition=payload.surface_condition,
    )
    db.add(event)
    db.flush()  # Assign event_id before hotspot logic

    # Run hotspot intelligence
    process_event_for_hotspot(db, event)

    db.commit()
    db.refresh(event)

    # ── Broadcast live event to all connected dashboard subscribers ──────────
    try:
        from app.services.ws_broadcaster import get_broadcaster
        event_ts = event.timestamp
        if event_ts.tzinfo is None:
            event_ts = event_ts.replace(tzinfo=timezone.utc)

        ws_payload = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "confidence": round(event.confidence, 4) if event.confidence is not None else 0.85,
            "severity": event.severity,
            "bus_id": event.bus_id,
            "camera_id": event.camera_id or "CAM_FRONT",
            "latitude": event.latitude,
            "longitude": event.longitude,
            "timestamp": event_ts.isoformat(),
            "evidence": event.evidence,
            "status": event.status or "new",
            "repeated_detections": event.repeated_detections or 1,
            "car_count": event.car_count,
            "bike_count": event.bike_count,
            "bus_count": event.bus_count,
            "truck_count": event.truck_count,
            "total_vehicles": event.total_vehicles,
            "density": event.density,
            "density_score": event.density_score,
            "width_ratio": event.width_ratio,
            "area_ratio": event.area_ratio,
            "severity_method": event.severity_method,
            "surface_condition": event.surface_condition,
        }
        await get_broadcaster().broadcast(ws_payload)
    except Exception as b_err:
        print(f"[EventsRouter] Failed to broadcast event {event.event_id}: {b_err}")

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
    return q.order_by(func.datetime(Event.timestamp).desc()).offset(offset).limit(limit).all()



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


@router.post("/seed-pr37", tags=["Events"])
def trigger_seed_pr37(db: Session = Depends(get_db)):
    """
    Ingests and seeds real PR 37 pothole detections into the database,
    triggers hotspot clustering, and returns ingestion statistics.
    """
    from app.seed import seed_pr37_potholes
    seeded_count = seed_pr37_potholes(db)
    return {
        "status": "ok",
        "message": f"Successfully seeded {seeded_count} PR 37 road defect events.",
        "events_seeded": seeded_count,
    }
