"""
schemas/hotspot.py
------------------
Pydantic schemas for Hotspot endpoints.
"""

from __future__ import annotations
from pydantic import BaseModel, computed_field, field_serializer
from typing import List, Optional
from datetime import datetime, timezone


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

    @field_serializer("first_seen", "last_seen", check_fields=False)
    def serialize_utc_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

