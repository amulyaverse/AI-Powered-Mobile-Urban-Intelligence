"""
routers/buses.py
----------------
Bus fleet endpoints.

GET    /api/buses                       — list all buses
GET    /api/buses/{bus_id}              — single bus
POST   /api/buses                       — register a new bus
PATCH  /api/buses/{bus_id}             — update route / status / camera_status
PUT    /api/buses/{bus_id}/location    — update GPS + traffic level (edge AI)
DELETE /api/buses/{bus_id}             — remove bus (rejected if it has linked events)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.bus import Bus
from app.schemas.bus import BusResponse, BusLocationUpdate, BusCreate, BusUpdate

router = APIRouter(prefix="/api/buses", tags=["Buses"])


@router.get("", response_model=List[BusResponse])
def list_buses(db: Session = Depends(get_db)):
    """Return all buses, ordered by last_seen descending."""
    return db.query(Bus).order_by(Bus.last_seen.desc().nullslast()).all()


@router.get("/{bus_id}", response_model=BusResponse)
def get_bus(bus_id: str, db: Session = Depends(get_db)):
    """Return a single bus by ID."""
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus


@router.post("", response_model=BusResponse, status_code=201)
def create_bus(payload: BusCreate, db: Session = Depends(get_db)):
    """
    Register a new bus in the fleet.
    Returns 409 if a bus with the same ID already exists.
    """
    existing = db.query(Bus).filter(Bus.id == payload.id).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A bus with ID '{payload.id}' already exists."
        )
    bus = Bus(
        id=payload.id,
        route=payload.route,
        status=payload.status,
        camera_status=payload.camera_status,
        last_traffic="Unknown",
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus


@router.patch("/{bus_id}", response_model=BusResponse)
def update_bus(bus_id: str, payload: BusUpdate, db: Session = Depends(get_db)):
    """
    Partially update a bus's editable administrative fields:
    route, status, camera_status.
    Only non-None fields in the payload are applied.
    """
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    if payload.route is not None:
        bus.route = payload.route
    if payload.status is not None:
        bus.status = payload.status
    if payload.camera_status is not None:
        bus.camera_status = payload.camera_status

    db.commit()
    db.refresh(bus)
    return bus


@router.put("/{bus_id}/location", response_model=BusResponse)
def update_bus_location(
    bus_id: str,
    payload: BusLocationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a bus's GPS position and traffic reading.
    Can be called by the edge AI alongside event posting.
    """
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    bus.last_lat = payload.lat
    bus.last_lng = payload.lng
    bus.last_traffic = payload.traffic or "Unknown"
    bus.last_seen = datetime.now(timezone.utc)

    db.commit()
    db.refresh(bus)
    return bus


@router.delete("/{bus_id}", status_code=204)
def delete_bus(bus_id: str, db: Session = Depends(get_db)):
    """
    Permanently remove a bus from the fleet.

    Returns 404 if the bus does not exist.
    Returns 409 if the bus has associated events — set status to 'Offline'
    to deactivate without losing historical data.
    """
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    # Guard against breaking event history
    event_count = bus.events.count()
    if event_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete bus '{bus_id}' — it has {event_count} associated event(s). "
                "Set the bus status to 'Offline' to deactivate it while preserving history."
            ),
        )

    db.delete(bus)
    db.commit()
    return None


