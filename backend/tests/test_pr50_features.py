"""
tests/test_pr50_features.py
----------------------------
Tests for PR #50 improvements:
  - Spatial cluster fusion (_fuse_pothole_boxes)
  - Camera WebSocket 4-byte frame_id header prefix extraction and response echoing
  - Backward compatibility with legacy raw JPEG payloads
"""

import struct
import cv2
import numpy as np
import pytest

from app.services.inference_engine import BoundingBox, _fuse_pothole_boxes
from tests.test_events import client, engine, TestingSessionLocal, override_get_db
from app.database import Base, get_db
from app.models.bus import Bus
from app.config import get_settings

settings = get_settings()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


def test_fuse_pothole_boxes_merging():
    """Verify _fuse_pothole_boxes clusters adjacent/overlapping boxes and retains max confidence."""
    # Two boxes within 60px distance threshold
    b1 = BoundingBox(x1=100.0, y1=100.0, x2=150.0, y2=150.0, class_name="pothole", confidence=0.75)
    b2 = BoundingBox(x1=160.0, y1=110.0, x2=210.0, y2=160.0, class_name="pothole", confidence=0.88)
    # A third distant box that should not merge
    b3 = BoundingBox(x1=400.0, y1=400.0, x2=450.0, y2=450.0, class_name="pothole", confidence=0.92)

    fused = _fuse_pothole_boxes([b1, b2, b3], distance_threshold=60)
    assert len(fused) == 2

    # Find the merged box
    merged = next(b for b in fused if b.x1 == 100.0)
    assert merged.x2 == 210.0
    assert merged.y1 == 100.0
    assert merged.y2 == 160.0
    assert merged.confidence == 0.88  # max confidence between b1 and b2

    # Distant box
    distant = next(b for b in fused if b.x1 == 400.0)
    assert distant.x2 == 450.0
    assert distant.confidence == 0.92


def test_camera_ws_with_frame_id_header():
    """Verify camera WebSocket extracts 4-byte uint32 frame_id and echoes it back."""
    db = TestingSessionLocal()
    try:
        bus = Bus(
            id="BUS_PR50_TEST",
            route="Route 100",
            status="Active",
            camera_status="Active",
            last_lat=28.6139,
            last_lng=77.2090,
        )
        db.add(bus)
        db.commit()

        with client.websocket_connect("/api/ws/camera/BUS_PR50_TEST?mode=traffic") as ws:
            # Create a blank JPEG frame
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            _, jpeg = cv2.imencode(".jpg", img)
            raw_jpeg = jpeg.tobytes()

            # Prepend 4-byte little-endian uint32 frame ID: 1042
            frame_id = 1042
            header = struct.pack("<I", frame_id)
            payload = header + raw_jpeg

            ws.send_bytes(payload)
            resp = ws.receive_json()

            assert "frame_id" in resp
            assert resp["frame_id"] == 1042
    finally:
        db.close()


def test_camera_ws_legacy_without_frame_id():
    """Verify camera WebSocket handles legacy raw JPEG bytes gracefully without frame_id header."""
    db = TestingSessionLocal()
    try:
        bus = Bus(
            id="BUS_PR50_LEGACY",
            route="Route 101",
            status="Active",
            camera_status="Active",
            last_lat=28.6139,
            last_lng=77.2090,
        )
        db.add(bus)
        db.commit()

        with client.websocket_connect("/api/ws/camera/BUS_PR50_LEGACY?mode=traffic") as ws:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            _, jpeg = cv2.imencode(".jpg", img)
            ws.send_bytes(jpeg.tobytes())
            resp = ws.receive_json()

            assert "frame_id" in resp
            assert resp["frame_id"] is None
    finally:
        db.close()
