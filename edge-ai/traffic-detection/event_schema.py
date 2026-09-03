"""
event_schema.py
---------------
Defines the TrafficEvent dataclass — the structured JSON output that the
Vehicle AI pipeline emits once per second and sends to the backend API.

This is the contract between Member 1 (Vehicle AI) and Member 3 (Backend).
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
import json
import time


@dataclass
class GPSCoordinate:
    lat: float = 0.0
    lon: float = 0.0

    def to_dict(self) -> dict:
        return {"lat": self.lat, "lon": self.lon}


@dataclass
class TrafficEvent:
    """
    One event emitted per EVENT_EMIT_INTERVAL_SEC of processed video.

    Example JSON output:
    {
        "event_type": "traffic_snapshot",
        "timestamp": 1725302400.0,
        "timestamp_iso": "2026-09-03T00:00:00",
        "bus_id": "BUS-042",
        "gps": { "lat": 12.9716, "lon": 77.5946 },
        "vehicle_counts": {
            "car": 18, "bike": 9, "bus": 2, "truck": 3
        },
        "total_vehicles": 32,
        "density": "HIGH",
        "density_score": 0.78,
        "frame_coverage_ratio": 0.22,
        "confidence": 0.87,
        "source_frame": 450
    }
    """
    event_type: str = "traffic_snapshot"
    timestamp: float = field(default_factory=time.time)
    timestamp_iso: str = ""
    bus_id: str = "BUS-UNKNOWN"
    gps: GPSCoordinate = field(default_factory=GPSCoordinate)

    vehicle_counts: Dict[str, int] = field(default_factory=lambda: {
        "car": 0, "bike": 0, "bus": 0, "truck": 0
    })
    total_vehicles: int = 0
    density: str = "LOW"           # LOW | MEDIUM | HIGH | CRITICAL
    density_score: float = 0.0     # 0.0 – 1.0 normalised score
    frame_coverage_ratio: float = 0.0  # fraction of frame area covered by bboxes
    confidence: float = 0.0        # mean detection confidence in this interval
    source_frame: int = 0          # frame index when this event was generated

    def __post_init__(self):
        if not self.timestamp_iso:
            import datetime
            self.timestamp_iso = datetime.datetime.fromtimestamp(
                self.timestamp
            ).strftime("%Y-%m-%dT%H:%M:%S")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["gps"] = self.gps.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Human-readable one-liner for terminal output."""
        c = self.vehicle_counts
        return (
            f"Cars: {c.get('car', 0):>3} | "
            f"Bikes: {c.get('bike', 0):>3} | "
            f"Buses: {c.get('bus', 0):>3} | "
            f"Trucks: {c.get('truck', 0):>3} | "
            f"Total: {self.total_vehicles:>3} | "
            f"Density: {self.density:<8} | "
            f"Conf: {self.confidence:.2f}"
        )
