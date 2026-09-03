"""
routers/buses.py
----------------
Bus fleet endpoints.

GET /api/buses                       — list all buses
GET /api/buses/{bus_id}              — single bus
PUT /api/buses/{bus_id}/location     — update GPS + traffic level
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.bus import Bus
from app.schemas.bus import BusResponse, BusLocationUpdate

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
