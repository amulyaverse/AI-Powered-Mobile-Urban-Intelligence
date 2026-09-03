"""
schemas/event.py
----------------
Pydantic v2 schemas for the Event API endpoints.

EventCreate  → validated body for POST /api/events
EventResponse → serialised response for GET endpoints
EventStatusUpdate → body for PATCH /api/events/{id}/status
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


# ── Allowed values ──────────────────────────────────────────────────────────

EVENT_TYPES = {"pothole", "road_defect", "congestion", "vehicle_count"}
SEVERITIES  = {"low", "medium", "high", "critical"}
STATUSES    = {"new", "under_review", "verified", "resolved"}
DENSITIES   = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


# ── Request schemas ──────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    """
    Body accepted by POST /api/events.
    
    This matches the integration contract from docs/api/event-schema.md.
    The event_id and status are assigned by the backend.
    """
    event_type: str = Field(..., description="pothole | road_defect | congestion | vehicle_count")
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(..., description="low | medium | high | critical")
    bus_id: str = Field(..., description="e.g. BUS_021")
    camera_id: Optional[str] = Field(default="CAM_FRONT")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: datetime
    evidence: Optional[str] = Field(default=None, description="URL or placeholder image path")

    # Optional traffic-specific fields (for vehicle_count events from traffic AI)
    car_count: Optional[int] = None
    bike_count: Optional[int] = None
    bus_count: Optional[int] = None
    truck_count: Optional[int] = None
    total_vehicles: Optional[int] = None
    density: Optional[str] = Field(default=None, description="LOW | MEDIUM | HIGH | CRITICAL")
    density_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type must be one of: {EVENT_TYPES}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in SEVERITIES:
            raise ValueError(f"severity must be one of: {SEVERITIES}")
        return v


class EventStatusUpdate(BaseModel):
    """Body accepted by PATCH /api/events/{event_id}/status."""
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in STATUSES:
            raise ValueError(f"status must be one of: {STATUSES}")
        return v


# ── Response schemas ─────────────────────────────────────────────────────────

class EventResponse(BaseModel):
    """Full event object returned by GET endpoints — matches frontend mock schema exactly."""
    event_id: str
    event_type: str
    confidence: float
    severity: str
    bus_id: Optional[str]
    camera_id: Optional[str]
    latitude: float
    longitude: float
    timestamp: datetime
    evidence: Optional[str]
    status: str
    repeated_detections: int
    hotspot_id: Optional[int]
    created_at: datetime

    # Traffic fields (None for non-vehicle_count events)
    car_count: Optional[int] = None
    bike_count: Optional[int] = None
    bus_count: Optional[int] = None
    truck_count: Optional[int] = None
    total_vehicles: Optional[int] = None
    density: Optional[str] = None
    density_score: Optional[float] = None

    model_config = {"from_attributes": True}
