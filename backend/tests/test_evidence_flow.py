"""
test_evidence_flow.py
----------------------
Verifies:
1. Static /evidence route serves saved evidence frames with HTTP 200.
2. REST ingestion copies local image files and assigns /evidence/{id}.jpg.
3. WebSocket camera frame ingestion saves decoded frames and populates evidence.
"""

import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
from pathlib import Path

from tests.test_events import client, setup_db
from app.config import get_settings
from app.routers.camera_ws import _ingest_event_sync
from app.services.inference_engine import InferenceResult, BoundingBox
settings = get_settings()

def test_static_evidence_mount():
    """Verify that images in settings.EVIDENCE_DIR are served via /evidence/..."""
    test_img = settings.EVIDENCE_DIR / "test_static_mount.jpg"
    # Create a small dummy image
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(test_img), dummy)

    try:
        resp = client.get("/evidence/test_static_mount.jpg")
        assert resp.status_code == 200
        assert resp.headers["content-type"] in ("image/jpeg", "application/octet-stream")
        assert len(resp.content) > 0
    finally:
        if test_img.exists():
            test_img.unlink()

def test_rest_ingest_local_evidence_file(tmp_path):
    """Verify that REST ingestion with a local image file copies it to EVIDENCE_DIR."""
    local_img = tmp_path / "local_capture.jpg"
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(str(local_img), dummy)

    payload = {
        "event_id": "EVT_TEST_LOCAL_IMG",
        "event_type": "pothole",
        "confidence": 0.90,
        "severity": "high",
        "bus_id": "BUS_01",
        "camera_id": "CAM_FRONT",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "evidence": str(local_img),
    }
    resp = client.post("/api/events", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["evidence"] == "/evidence/EVT_TEST_LOCAL_IMG.jpg"

    saved_file = settings.EVIDENCE_DIR / "EVT_TEST_LOCAL_IMG.jpg"
    assert saved_file.exists()
    saved_file.unlink()

def test_camera_ws_frame_persistence():
    """Verify that _ingest_event_sync saves frame and sets evidence path."""
    frame = np.full((360, 640, 3), 120, dtype=np.uint8)
    dummy_result = InferenceResult(
        event_type="pothole",
        confidence=0.91,
        severity="high",
        frame_index=42,
        frame_coverage_ratio=0.08,
        boxes=[BoundingBox(x1=100.0, y1=150.0, x2=200.0, y2=250.0, class_name="pothole", confidence=0.91)],
        width_ratio=0.156,
        area_ratio=0.043,
        severity_method="width_heuristic_pr37",
        surface_condition="pothole",
    )

    evt = _ingest_event_sync(
        bus_id="BUS_01",
        lat=28.62,
        lng=77.21,
        result=dummy_result,
        ws_session_id=None,
        frame=frame,
    )

    assert evt.evidence is not None
    assert evt.evidence.startswith("/evidence/")
    assert evt.evidence.endswith(".jpg")

    saved_path = settings.EVIDENCE_DIR / f"{evt.event_id}.jpg"
    assert saved_path.exists()

    # Verify WS payload contains evidence
    payload = dummy_result.to_ws_payload(event_id=evt.event_id, evidence=evt.evidence)
    assert payload["evidence"] == evt.evidence

    # Clean up
    if saved_path.exists():
        saved_path.unlink()
