"""
schemas/hotspot.py
------------------
Pydantic schemas for Hotspot endpoints.
"""

from __future__ import annotations
from pydantic import BaseModel, computed_field
from typing import List
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
    event_ids: List[str] = []

    # Compatibility aliases for integration contract & stub callers
    @computed_field
    @property
    def latitude(self) -> float:
        return self.center_lat

    @computed_field
    @property
    def longitude(self) -> float:
        return self.center_lng

    @computed_field
    @property
    def report_count(self) -> int:
        return self.detection_count

    @computed_field
    @property
    def max_severity(self) -> str:
        return self.severity

    model_config = {"from_attributes": True}
