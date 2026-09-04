"""
schemas/bus.py
--------------
Pydantic schemas for Bus endpoints.
"""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    created_at: datetime

    model_config = {"from_attributes": True}


class BusLocationUpdate(BaseModel):
    """Body for PUT /api/buses/{bus_id}/location."""
    lat: float
    lng: float
    traffic: Optional[str] = "Unknown"  # Low | Medium | High | Unknown
