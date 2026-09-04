"""
End-to-end smoke test for the integration pipeline.

Start the backend first (in another terminal):
    cd backend
    uvicorn app.main:app --reload --port 8000


Then run this from the repo root:
    python integration/test_pipeline.py

Replace the fake_*_detection() functions below with real calls into
Pranav's and Abhinandan's model functions once you're ready to plug
them in -- event_generator.process_detection() doesn't care where
the dict comes from, only that it matches the schema.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / "event-generator"))
from event_generator import process_detection  # noqa: E402


def fake_traffic_detection():
    """Stand-in for Pranav's vehicle-counting / congestion output."""
    return {
        "event_type": "congestion",
        "confidence": 0.81,
        "severity": "medium",
        "evidence": "/tmp/frame_congestion_001.jpg",
    }


def fake_pothole_detection():
    """Stand-in for Abhinandan's pothole model output."""
    return {
        "event_type": "pothole",
        "confidence": 0.93,
        "severity": "high",
        "evidence": "/tmp/frame_pothole_004.jpg",
    }


def fake_low_confidence_detection():
    """Should be discarded -- below the 0.65 threshold."""
    return {
        "event_type": "pothole",
        "confidence": 0.42,
        "severity": "low",
        "evidence": "/tmp/frame_pothole_099.jpg",
    }


if __name__ == "__main__":
    print("Running pipeline smoke test...\n")
    process_detection(fake_traffic_detection())
    process_detection(fake_pothole_detection())
    process_detection(fake_low_confidence_detection())
    print("\nDone. Check http://localhost:8000/api/events to see stored events.")
    print("Hotspots (needs >=2 nearby defect reports): http://localhost:8000/api/hotspots")
