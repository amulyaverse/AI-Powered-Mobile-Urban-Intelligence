"""
tests/test_bus_delhi_vicinity.py
---------------------------------
Tests for Delhi coordinate randomization on server startup and 3km vicinity enforcement
for all detections associated with the target bus.
"""

import pytest
from datetime import datetime, timezone

from app.main import app
from app.database import Base, get_db
from app.models.bus import Bus
from app.models.event import Event
from app.config import get_settings
from app.services.bus_location_service import (
    DELHI_BOUNDS,
    get_random_delhi_coordinates,
    get_vicinity_coordinates,
    haversine_distance_km,
    randomize_bus_on_startup,
)
from tests.test_events import client, engine, TestingSessionLocal, override_get_db

settings = get_settings()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


def test_random_delhi_coordinates_within_bounds():
    """Verify get_random_delhi_coordinates produces valid Delhi NCR coordinates."""
    for _ in range(50):
        lat, lng, name = get_random_delhi_coordinates()
        assert DELHI_BOUNDS["min_lat"] <= lat <= DELHI_BOUNDS["max_lat"], f"Lat {lat} out of Delhi bounds"
        assert DELHI_BOUNDS["min_lng"] <= lng <= DELHI_BOUNDS["max_lng"], f"Lng {lng} out of Delhi bounds"
        assert len(name) > 0


def test_vicinity_coordinates_strictly_within_3km():
    """Verify get_vicinity_coordinates guarantees distance <= 3.0 km across iterations."""
    base_lat, base_lng, _ = get_random_delhi_coordinates()
    max_radius_km = 3.0

    for step in range(100):
        vic_lat, vic_lng = get_vicinity_coordinates(base_lat, base_lng, max_radius_km=max_radius_km, step=step)
        dist = haversine_distance_km(base_lat, base_lng, vic_lat, vic_lng)
        assert dist <= max_radius_km + 1e-4, f"Distance {dist} exceeds max radius {max_radius_km} km at step {step}"


def test_randomize_bus_on_startup_and_detection_vicinity():
    """Verify randomize_bus_on_startup places the bus in Delhi and all its detections within 3km."""
    db = TestingSessionLocal()
    try:
        test_bus_id = "BUS_021"

        # Create bus
        bus = Bus(id=test_bus_id, route="Route 534", status="Active", camera_status="Active")
        db.add(bus)
        db.commit()

        # Add dummy events far away
        evt1 = Event(
            event_id="EVT_VIC_TEST_1",
            event_type="pothole",
            confidence=0.90,
            severity="high",
            bus_id=test_bus_id,
            camera_id="CAM_FRONT",
            latitude=12.9716,  # Bangalore (far away)
            longitude=77.5946,
            timestamp=datetime.now(timezone.utc),
            status="new",
        )
        evt2 = Event(
            event_id="EVT_VIC_TEST_2",
            event_type="congestion",
            confidence=0.88,
            severity="medium",
            bus_id=test_bus_id,
            camera_id="CAM_FRONT",
            latitude=19.0760,  # Mumbai (far away)
            longitude=72.8777,
            timestamp=datetime.now(timezone.utc),
            status="verified",
        )
        db.add(evt1)
        db.add(evt2)
        db.commit()

        # Run startup randomization
        summary = randomize_bus_on_startup(db, test_bus_id, max_radius_km=3.0)

        assert summary["bus_id"] == test_bus_id
        bus_lat = summary["lat"]
        bus_lng = summary["lng"]
        assert DELHI_BOUNDS["min_lat"] <= bus_lat <= DELHI_BOUNDS["max_lat"]
        assert DELHI_BOUNDS["min_lng"] <= bus_lng <= DELHI_BOUNDS["max_lng"]

        # Check that bus in DB matches
        db_bus = db.query(Bus).filter(Bus.id == test_bus_id).first()
        assert db_bus.last_lat == bus_lat
        assert db_bus.last_lng == bus_lng

        # Verify all events for this bus are now within 3 km of the new bus location
        bus_events = db.query(Event).filter(Event.bus_id == test_bus_id).all()
        assert len(bus_events) >= 2
        for e in bus_events:
            d = haversine_distance_km(bus_lat, bus_lng, e.latitude, e.longitude)
            assert d <= 3.01, f"Event {e.event_id} at ({e.latitude}, {e.longitude}) is {d:.2f} km away (> 3 km)"

    finally:
        db.close()


def test_post_event_target_bus_snaps_to_vicinity():
    """Verify POST /api/events for TARGET_BUS_ID snaps far coordinates to the 3km vicinity."""
    db = TestingSessionLocal()
    try:
        # Pre-populate the target bus at Delhi coordinates
        lat, lng, _ = get_random_delhi_coordinates()
        bus = Bus(
            id=settings.TARGET_BUS_ID,
            route="Route 534",
            status="Active",
            camera_status="Active",
            last_lat=lat,
            last_lng=lng,
        )
        db.add(bus)
        db.commit()

        # Post an event with coordinates far away
        payload = {
            "event_id": "EVT_VIC_POST_TEST",
            "event_type": "pothole",
            "confidence": 0.95,
            "severity": "high",
            "bus_id": settings.TARGET_BUS_ID,
            "camera_id": "CAM_FRONT",
            "latitude": 28.0000,   # ~60 km away
            "longitude": 77.0000,
            "status": "new",
        }
        res = client.post("/api/events", json=payload)
        assert res.status_code == 201
        data = res.json()

        # The ingested event should be within 3 km of the bus
        evt_lat = data["latitude"]
        evt_lng = data["longitude"]
        dist = haversine_distance_km(lat, lng, evt_lat, evt_lng)
        assert dist <= 3.01, f"Ingested event distance {dist:.2f} km exceeds 3 km vicinity"

    finally:
        db.close()


def test_camera_ws_resolves_bus_delhi_coordinates():
    """Verify camera WebSocket resolves the bus's active Delhi coordinates and handles frame stream."""
    import cv2
    import numpy as np

    db = TestingSessionLocal()
    try:
        lat, lng, _ = get_random_delhi_coordinates()
        bus = Bus(
            id=settings.TARGET_BUS_ID,
            route="Route 534",
            status="Active",
            camera_status="Active",
            last_lat=lat,
            last_lng=lng,
        )
        db.add(bus)
        db.commit()

        # Connect WebSocket without passing lat/lng - backend resolves it from DB
        with client.websocket_connect(f"/api/ws/camera/{settings.TARGET_BUS_ID}?mode=traffic") as ws:
            # Create a blank JPEG frame
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            _, jpeg = cv2.imencode(".jpg", img)
            ws.send_bytes(jpeg.tobytes())
            resp = ws.receive_json()
            # Status should be frame response (no_detection or detection)
            assert "status" in resp or "event_id" in resp
            if "latitude" in resp:
                d = haversine_distance_km(lat, lng, resp["latitude"], resp["longitude"])
                assert d <= 3.01
    finally:
        db.close()

