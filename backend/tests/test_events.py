"""
tests/test_events.py
--------------------
Unit tests for the events API endpoints.

Uses an in-memory SQLite database — no external DB required to run tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ── In-memory SQLite test DB ──────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

# ── Valid event payload ───────────────────────────────────────────────────────
VALID_EVENT = {
    "event_type": "pothole",
    "confidence": 0.87,
    "severity": "high",
    "bus_id": "BUS_021",
    "camera_id": "CAM_FRONT",
    "latitude": 28.5639,
    "longitude": 77.2090,
    "timestamp": "2026-09-03T10:42:17Z",
    "evidence": "https://example.com/frame.jpg",
}


class TestEventIngestion:
    def test_post_valid_event_returns_201(self):
        resp = client.post("/api/events", json=VALID_EVENT)
        assert resp.status_code == 201
        data = resp.json()
        assert data["event_type"] == "pothole"
        assert data["status"] == "new"
        assert "event_id" in data

    def test_post_low_confidence_rejected(self):
        payload = {**VALID_EVENT, "confidence": 0.30}
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 422

    def test_post_invalid_event_type_rejected(self):
        payload = {**VALID_EVENT, "event_type": "unknown_type"}
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 422

    def test_post_invalid_severity_rejected(self):
        payload = {**VALID_EVENT, "severity": "catastrophic"}
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 422


class TestEventRetrieval:
    def test_list_events_empty(self):
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_events_returns_posted_event(self):
        client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/events")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_event_by_id(self):
        post_resp = client.post("/api/events", json=VALID_EVENT)
        event_id = post_resp.json()["event_id"]
        resp = client.get(f"/api/events/{event_id}")
        assert resp.status_code == 200
        assert resp.json()["event_id"] == event_id

    def test_get_event_not_found(self):
        resp = client.get("/api/events/nonexistent-id")
        assert resp.status_code == 404

    def test_filter_events_by_type(self):
        client.post("/api/events", json=VALID_EVENT)
        client.post("/api/events", json={**VALID_EVENT, "event_type": "congestion"})
        resp = client.get("/api/events?event_type=pothole")
        assert all(e["event_type"] == "pothole" for e in resp.json())


class TestEventStatusUpdate:
    def test_update_status_to_verified(self):
        post_resp = client.post("/api/events", json=VALID_EVENT)
        event_id = post_resp.json()["event_id"]
        resp = client.patch(f"/api/events/{event_id}/status", json={"status": "verified"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "verified"

    def test_update_status_invalid_value(self):
        post_resp = client.post("/api/events", json=VALID_EVENT)
        event_id = post_resp.json()["event_id"]
        resp = client.patch(f"/api/events/{event_id}/status", json={"status": "deleted"})
        assert resp.status_code == 422


class TestHotspotLogic:
    def test_repeated_detections_same_location(self):
        """Three events at same GPS → repeated_detections should reach 3."""
        for _ in range(3):
            client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/events")
        events = resp.json()
        max_repeated = max(e["repeated_detections"] for e in events)
        assert max_repeated >= 3

    def test_hotspot_created_after_events(self):
        for _ in range(2):
            client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/hotspots")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_alert_generated_at_threshold(self):
        """3 pothole events at same location → system alert should be created."""
        for _ in range(3):
            client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/alerts")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestBusEndpoints:
    def test_bus_auto_registered_on_event(self):
        client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/buses/BUS_021")
        assert resp.status_code == 200
        assert resp.json()["id"] == "BUS_021"

    def test_list_buses(self):
        client.post("/api/events", json=VALID_EVENT)
        resp = client.get("/api/buses")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestAnalyticsEndpoints:
    def test_summary_returns_correct_shape(self):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "activeBuses" in data
        assert "eventsToday" in data
        assert "potholesDetected" in data
        assert "trafficHotspots" in data
        assert "criticalAlerts" in data

    def test_traffic_analytics_shape(self):
        resp = client.get("/api/analytics/traffic")
        assert resp.status_code == 200
        data = resp.json()
        assert "densityOverTime" in data
        assert "vehicleTypes" in data
        assert "routes" in data

    def test_road_analytics_shape(self):
        resp = client.get("/api/analytics/road")
        assert resp.status_code == 200
        data = resp.json()
        assert "severityDistribution" in data
        assert "defectsOverTime" in data

    def test_traffic_summary_endpoint(self):
        resp = client.get("/api/analytics/traffic/summary")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["totalVehicles", "avgTrafficDensity", "congestionHotspots", "criticalHotspots", "monitoringFleet", "activeCameras"]:
            assert field in data

    def test_road_summary_endpoint(self):
        resp = client.get("/api/analytics/road/summary")
        assert resp.status_code == 200
        data = resp.json()
        for field in ["totalPotholes", "highSeverityIssues", "persistentDefects", "resolvedDefects"]:
            assert field in data


class TestEventSearchAndFilter:
    def test_search_and_bus_filter(self):
        payload1 = {
            "event_type": "pothole",
            "confidence": 0.88,
            "severity": "high",
            "bus_id": "BUS_SEARCH_1",
            "camera_id": "CAM_FRONT",
            "latitude": 28.5639,
            "longitude": 77.2090,
            "timestamp": "2026-09-03T10:00:00Z",
        }
        payload2 = {
            "event_type": "congestion",
            "confidence": 0.90,
            "severity": "medium",
            "bus_id": "BUS_OTHER_2",
            "camera_id": "CAM_FRONT",
            "latitude": 28.5640,
            "longitude": 77.2091,
            "timestamp": "2026-09-03T10:05:00Z",
        }
        r1 = client.post("/api/events", json=payload1)
        r2 = client.post("/api/events", json=payload2)
        assert r1.status_code == 201
        assert r2.status_code == 201

        # Test bus_id filter
        res = client.get("/api/events?bus_id=BUS_SEARCH_1")
        assert res.status_code == 200
        items = res.json()
        assert len(items) >= 1
        assert all(i["bus_id"] == "BUS_SEARCH_1" for i in items)

        # Test search
        res_search = client.get("/api/events?search=SEARCH_1")
        assert res_search.status_code == 200
        search_items = res_search.json()
        assert any(i["bus_id"] == "BUS_SEARCH_1" for i in search_items)


class TestAlertAcknowledge:
    def test_acknowledge_alert(self):
        # Generate an alert by posting 3 events at the same spot
        for i in range(3):
            client.post("/api/events", json={
                "event_type": "pothole",
                "confidence": 0.85,
                "severity": "high",
                "bus_id": "BUS_ACK_TEST",
                "camera_id": "CAM_FRONT",
                "latitude": 28.5555,
                "longitude": 77.2222,
                "timestamp": "2026-09-03T11:00:00Z",
            })
        alerts = client.get("/api/alerts?acknowledged=false").json()
        assert len(alerts) > 0
        target_id = alerts[0]["id"]
        ack_res = client.patch(f"/api/alerts/{target_id}/acknowledge")
        assert ack_res.status_code == 200
        assert ack_res.json()["acknowledged"] is True


