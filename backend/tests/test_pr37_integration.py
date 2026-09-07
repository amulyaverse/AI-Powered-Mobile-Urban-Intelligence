"""
tests/test_pr37_integration.py
-------------------------------
Tests for PR 37 Pothole AI integration:
  - Video samples listing and stream endpoint
  - PR 37 pothole schema fields (bbox, width_ratio, area_ratio, severity_method)
  - PR 37 database seeding and hotspot clustering
"""

import pytest
from app.database import Base, get_db
from tests.test_events import client, engine, TestingSessionLocal, override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


def test_list_sample_videos():
    """Verify PR 37 sample videos endpoint returns available videos."""
    response = client.get("/api/videos/samples")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    filenames = [v["filename"] for v in data]
    assert "cityRoad_potHoles.mp4" in filenames
    assert "ruralRoad_potHoles.mp4" in filenames


def test_stream_sample_video():
    """Verify streaming a valid PR 37 sample video returns video/mp4."""
    response = client.get("/api/videos/stream/cityRoad_potHoles.mp4")
    assert response.status_code in (200, 206)
    assert "video/mp4" in response.headers.get("content-type", "")
    assert "accept-ranges" in response.headers

def test_stream_sample_video_range_request():
    """Verify HTTP Range requests return 206 with Content-Range."""
    response = client.get(
        "/api/videos/stream/cityRoad_potHoles.mp4",
        headers={"Range": "bytes=0-1023"}
    )
    assert response.status_code == 206
    assert "video/mp4" in response.headers.get("content-type", "")
    assert "content-range" in response.headers
    assert response.headers["content-range"].startswith("bytes 0-1023/")
    assert len(response.content) == 1024


def test_stream_nonexistent_video():
    """Verify requesting non-existent video returns 404."""
    response = client.get("/api/videos/stream/non_existent.mp4")
    assert response.status_code == 404


def test_ingest_pothole_event_with_pr37_fields():
    """Verify ingesting a pothole event preserves bbox, width_ratio, and area_ratio."""
    payload = {
        "event_id": "EVT_TEST_PR37_01",
        "event_type": "pothole",
        "confidence": 0.88,
        "severity": "high",
        "bus_id": "BUS_01",
        "latitude": 28.6289,
        "longitude": 77.2150,
        "bbox": [120, 200, 310, 380],
        "width_ratio": 0.297,
        "area_ratio": 0.075,
        "severity_method": "width_heuristic_pr37",
        "surface_condition": "pothole",
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == "EVT_TEST_PR37_01"
    assert data["event_type"] == "pothole"
    assert data["width_ratio"] == 0.297
    assert data["area_ratio"] == 0.075
    assert data["severity_method"] == "width_heuristic_pr37"


def test_seed_pr37_endpoint():
    """Verify POST /api/events/seed-pr37 triggers seeding and creates events."""
    response = client.post("/api/events/seed-pr37")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["events_seeded"] > 0
