"""
schemas/hotspot.py
------------------
Pydantic schemas for Hotspot endpoints.
"""

from pydantic import BaseModel
from datetime import datetime


class HotspotResponse(BaseModel):
    id: int
    center_lat: float
    center_lng: float
    event_type: str
    detection_count: int
    severity: str
    priority_score: float
    first_seen: datetime
    last_seen: datetime
    status: str

    model_config = {"from_attributes": True}
