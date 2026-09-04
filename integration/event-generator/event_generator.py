"""
Integration layer: wraps a raw AI-module detection dict into a
schema-compliant event and POSTs it to the backend.

This is the 'glue' described in docs/api/event-schema.md under
'Integration Layer Output' -- built here so the pipeline isn't
blocked on any single person's module being finished.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

sys.path.append(str(Path(__file__).resolve().parents[1] / "gps"))
from gps_simulator import GPSSimulator  # noqa: E402

BACKEND_URL = "http://localhost:8000/api/events"
MIN_CONFIDENCE = 0.65  # per docs/api/event-schema.md

# Config -- change per bus/camera when running on real hardware
BUS_ID = "BUS_021"
CAMERA_ID = "CAM_FRONT"

_gps = GPSSimulator()


def build_event(ai_output: dict) -> Optional[dict]:
    """
    ai_output: dict produced by an AI module (Pranav's traffic AI or
    Abhinandan's road AI), matching the 'AI Module Output' contract:
        {
            "event_type": "...",     # e.g. "congestion", "pothole"
            "confidence": 0.0-1.0,
            "severity": "...",
            "evidence": "path/to/frame.jpg",
        }
    bus_id / camera_id / latitude / longitude / timestamp / event_id /
    status are all filled in here, at the integration layer.

    Returns None if confidence is below threshold (event discarded).
    """
    if ai_output["confidence"] < MIN_CONFIDENCE:
        return None

    lat, lon = _gps.next()

    return {
        "event_id": f"EVT_{uuid.uuid4().hex[:8]}",
        "event_type": ai_output["event_type"],
        "confidence": ai_output["confidence"],
        "severity": ai_output["severity"],
        "bus_id": ai_output.get("bus_id", BUS_ID),
        "camera_id": ai_output.get("camera_id", CAMERA_ID),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evidence": ai_output.get("evidence", ""),
        "status": "new",
    }


def send_event(event: dict) -> requests.Response:
    return requests.post(BACKEND_URL, json=event, timeout=5)


def process_detection(ai_output: dict) -> Optional[dict]:
    """
    Call this once per AI detection (once per frame that produced a
    hit). Returns the backend's stored event, or None if the
    detection was discarded for low confidence.
    """
    event = build_event(ai_output)
    if event is None:
        print(f"[skip] confidence {ai_output['confidence']:.2f} below threshold")
        return None

    resp = send_event(event)
    resp.raise_for_status()
    print(f"[sent] {event['event_id']} ({event['event_type']}, conf={event['confidence']:.2f})")
    return resp.json()
