"""
schemas/bus.py
--------------
Pydantic schemas for Bus endpoints.
"""

from __future__ import annotations
from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional
from datetime import datetime, timezone


class BusCreate(BaseModel):
    """Body for POST /api/buses — register a new bus in the fleet."""
    id: str                                          # e.g. "BUS_099"
    route: Optional[str] = None                      # e.g. "Route 534"
    status: str = "Active"                           # Active | Maintenance | Offline
    camera_status: str = "Active"                    # Active | Offline

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Bus ID cannot be empty")
        if len(v) > 20:
            raise ValueError("Bus ID must be 20 characters or fewer")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Active", "Maintenance", "Offline"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("camera_status")
    @classmethod
    def validate_camera_status(cls, v: str) -> str:
        allowed = {"Active", "Offline"}
        if v not in allowed:
            raise ValueError(f"camera_status must be one of: {', '.join(sorted(allowed))}")
        return v


class BusUpdate(BaseModel):
    """Body for PATCH /api/buses/{bus_id} — partial update of editable fields."""
    route: Optional[str] = None
    status: Optional[str] = None
    camera_status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"Active", "Maintenance", "Offline"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("camera_status")
    @classmethod
    def validate_camera_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"Active", "Offline"}
        if v not in allowed:
            raise ValueError(f"camera_status must be one of: {', '.join(sorted(allowed))}")
        return v


class BusResponse(BaseModel):
    """Matches the frontend mock bus shape from mockData.js."""
    id: str
    route: Optional[str]
    status: str
    camera_status: str
    last_lat: Optional[float]
    last_lng: Optional[float]
    last_traffic: str
    last_seen: Optional[datetime]
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

    @field_serializer("last_seen", "created_at", check_fields=False)
    def serialize_utc_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class BusLocationUpdate(BaseModel):
    """Body for PUT /api/buses/{bus_id}/location."""
    lat: float
    lng: float
    traffic: Optional[str] = "Unknown"  # Low | Medium | High | Unknown
