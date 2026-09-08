"""
schemas/event.py
----------------
Pydantic v2 schemas for the Event API endpoints.

EventCreate  → validated body for POST /api/events
EventResponse → serialised response for GET endpoints
EventStatusUpdate → body for PATCH /api/events/{id}/status
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, model_validator, field_serializer
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid


# ── Allowed values ──────────────────────────────────────────────────────────

EVENT_TYPES = {"pothole", "road_defect", "congestion", "vehicle_count", "traffic_snapshot", "pothole_resolved", "traffic", "crack"}
SEVERITIES  = {"low", "medium", "high", "critical"}
STATUSES    = {"new", "under_review", "verified", "resolved"}
DENSITIES   = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


# ── Request schemas ──────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    """
    Body accepted by POST /api/events.
    
    Compatible with:
      - docs/api/event-schema.md integration contract
      - integration/event-generator/event_generator.py output
      - edge-ai/traffic-detection/ TrafficEvent dataclass output
    """
    event_id: Optional[str] = Field(default=None, description="Optional unique identifier (EVT_<hex> or UUID)")
    event_type: str = Field(..., description="pothole | road_defect | congestion | vehicle_count | traffic_snapshot")
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(default="low", description="low | medium | high | critical")
    bus_id: str = Field(default="BUS_021", description="e.g. BUS_021")
    camera_id: Optional[str] = Field(default="CAM_FRONT")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: Optional[str] = Field(default=None, description="URL or placeholder image path")
    status: Optional[str] = Field(default="new", description="new | under_review | verified | resolved")

    # Optional traffic-specific fields (for vehicle_count events from traffic AI)
    car_count: Optional[int] = None
    bike_count: Optional[int] = None
    bus_count: Optional[int] = None
    truck_count: Optional[int] = None
    total_vehicles: Optional[int] = None
    density: Optional[str] = Field(default=None, description="LOW | MEDIUM | HIGH | CRITICAL")
    density_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source_frame: Optional[int] = None
    frame_coverage_ratio: Optional[float] = None

    # PR 37 & 40: Pothole / road defect telemetry fields
    bbox: Optional[Any] = None
    width_ratio: Optional[float] = None
    area_ratio: Optional[float] = None
    severity_method: Optional[str] = None
    surface_condition: Optional[str] = None

    # Nested helper inputs for edge-AI adapters
    gps: Optional[Dict[str, float]] = None
    vehicle_counts: Optional[Dict[str, int]] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # 1. Normalize event_type
        raw_type = d.get("event_type")
        if isinstance(raw_type, str):
            raw_lower = raw_type.lower()
            if raw_lower in ("traffic_snapshot", "trafficsnapshot", "congestion"):
                d["event_type"] = "vehicle_count"
            else:
                d["event_type"] = raw_lower

        # 2. Extract coordinates from nested gps dict if latitude/longitude omitted
        if "gps" in d and isinstance(d["gps"], dict):
            gps_data = d["gps"]
            if "latitude" not in d or d["latitude"] is None:
                d["latitude"] = gps_data.get("lat", gps_data.get("latitude"))
            if "longitude" not in d or d["longitude"] is None:
                d["longitude"] = gps_data.get("lon", gps_data.get("longitude"))

        # Fallback default coordinates for raw PR 37 telemetry logs missing GPS
        if d.get("latitude") is None:
            d["latitude"] = 28.6139
        if d.get("longitude") is None:
            d["longitude"] = 77.2090

        # 3. Unpack nested vehicle_counts dict if provided
        if "vehicle_counts" in d and isinstance(d["vehicle_counts"], dict):
            vc = d["vehicle_counts"]
            if d.get("car_count") is None:
                d["car_count"] = vc.get("car", 0)
            if d.get("bike_count") is None:
                d["bike_count"] = vc.get("bike", 0)
            if d.get("bus_count") is None:
                d["bus_count"] = vc.get("bus", 0)
            if d.get("truck_count") is None:
                d["truck_count"] = vc.get("truck", 0)
            if d.get("total_vehicles") is None:
                d["total_vehicles"] = (
                    (d.get("car_count") or 0)
                    + (d.get("bike_count") or 0)
                    + (d.get("bus_count") or 0)
                    + (d.get("truck_count") or 0)
                )

        # 4. Normalize severity
        raw_severity = d.get("severity")
        if isinstance(raw_severity, str):
            sev_norm = raw_severity.strip().lower().replace("-", "_").replace(" ", "_")
            if sev_norm in ("very_high", "veryhigh"):
                d["severity"] = "critical"
            else:
                d["severity"] = sev_norm
        elif not raw_severity:
            # Fallback to density if present (e.g. from TrafficEvent)
            density = d.get("density")
            if isinstance(density, str):
                dens_norm = density.strip().lower().replace("-", "_").replace(" ", "_")
                if dens_norm in ("very_high", "veryhigh"):
                    d["severity"] = "critical"
                elif dens_norm in SEVERITIES:
                    d["severity"] = dens_norm
                else:
                    d["severity"] = "low"
            else:
                d["severity"] = "low"

        # 5. Timestamp handling (epoch seconds, timestamp_iso, space string, or ISO string)
        raw_ts = d.get("timestamp")
        if isinstance(raw_ts, (int, float)):
            d["timestamp"] = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        elif isinstance(raw_ts, str):
            try:
                if " " in raw_ts and "T" not in raw_ts:
                    d["timestamp"] = datetime.fromisoformat(raw_ts.replace(" ", "T")).replace(tzinfo=timezone.utc)
            except Exception:
                pass
        elif raw_ts is None and "timestamp_iso" in d:
            d["timestamp"] = d["timestamp_iso"]

        # 6. Bounding box formatting
        raw_bbox = d.get("bbox")
        if isinstance(raw_bbox, (list, tuple)):
            import json
            d["bbox"] = json.dumps([round(float(v), 2) for v in raw_bbox])

        # 7. Status default
        if not d.get("status"):
            d["status"] = "new"

        return d

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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> str:
        if v and v not in STATUSES:
            raise ValueError(f"status must be one of: {STATUSES}")
        return v or "new"


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
    repeated_detections: int = 1
    hotspot_id: Optional[int] = None
    created_at: Optional[datetime] = None

    # Traffic fields (None for non-vehicle_count events)
    car_count: Optional[int] = None
    bike_count: Optional[int] = None
    bus_count: Optional[int] = None
    truck_count: Optional[int] = None
    total_vehicles: Optional[int] = None
    density: Optional[str] = None
    density_score: Optional[float] = None
    source_frame: Optional[int] = None
    frame_coverage_ratio: Optional[float] = None

    # Road damage fields (PR 37 & 40)
    bbox: Optional[str] = None
    width_ratio: Optional[float] = None
    area_ratio: Optional[float] = None
    severity_method: Optional[str] = None
    surface_condition: Optional[str] = None
    ws_session_id: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_serializer("timestamp", "created_at", check_fields=False)
    def serialize_utc_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
