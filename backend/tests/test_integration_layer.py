"""
tests/test_integration_layer.py
-------------------------------
Tests verifying seamless compatibility with:
  1. Integration layer (event_generator.py, sample_route.csv, test_pipeline.py)
  2. Edge-AI Vehicle Detection pipeline (TrafficEvent dataclass output)
  3. Shared contract in docs/api/event-schema.md
"""

import pytest
from app.main import app
from app.database import Base, get_db
from tests.test_events import client, engine, TestingSessionLocal, override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


class TestIntegrationCompatibility:
    def test_post_event_with_client_event_id_and_status(self):
        """Integration layer sends event_id and status — verify they are preserved."""
        payload = {
            "event_id": "EVT_custom99",
            "event_type": "pothole",
            "confidence": 0.88,
            "severity": "high",
            "bus_id": "BUS_021",
            "camera_id": "CAM_FRONT",
            "latitude": 28.5639,
            "longitude": 77.2090,
            "timestamp": "2026-09-04T12:00:00Z",
            "evidence": "/evidence/test.jpg",
            "status": "new",
        }
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["event_id"] == "EVT_custom99"
        assert data["status"] == "new"

    def test_post_traffic_snapshot_maps_to_vehicle_count(self):
        """Member 1's TrafficEvent uses event_type='traffic_snapshot'."""
        payload = {
            "event_type": "traffic_snapshot",
            "confidence": 0.85,
            "severity": "medium",
            "bus_id": "BUS_021",
            "latitude": 28.6139,
            "longitude": 77.2090,
        }
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["event_type"] == "vehicle_count"

    def test_post_with_nested_gps_and_vehicle_counts(self):
        """Direct TrafficEvent ingestion with nested gps and vehicle_counts."""
        payload = {
            "event_type": "traffic_snapshot",
            "confidence": 0.91,
            "density": "HIGH",
            "bus_id": "BUS_042",
            "gps": {"lat": 28.6239, "lon": 77.2190},
            "vehicle_counts": {"car": 18, "bike": 9, "bus": 2, "truck": 3},
            "source_frame": 450,
            "frame_coverage_ratio": 0.22,
            "timestamp": 1725302400.0,
        }
        resp = client.post("/api/events", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["latitude"] == 28.6239
        assert data["longitude"] == 77.2190
        assert data["severity"] == "high"
        assert data["car_count"] == 18
        assert data["bike_count"] == 9
        assert data["bus_count"] == 2
        assert data["truck_count"] == 3
        assert data["total_vehicles"] == 32
        assert data["source_frame"] == 450
        assert data["frame_coverage_ratio"] == 0.22

    def test_analytics_summary_contains_both_kpi_and_breakdown(self):
        """Verify GET /api/analytics/summary returns KPI cards and breakdown."""
        client.post("/api/events", json={
            "event_type": "pothole",
            "confidence": 0.90,
            "severity": "high",
            "bus_id": "BUS_021",
            "latitude": 28.5639,
            "longitude": 77.2090,
        })
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        # Frontend KPI fields
        assert "activeBuses" in data
        assert "eventsToday" in data
        assert "potholesDetected" in data
        # Integration contract fields
        assert data["total_events"] >= 1
        assert "by_type" in data
        assert data["by_type"].get("pothole", 0) >= 1
        assert "by_severity" in data
        assert data["by_severity"].get("high", 0) >= 1

    def test_hotspots_response_contains_gis_and_stub_fields(self):
        """Verify GET /api/hotspots provides both center_lat and latitude, report_count, event_ids."""
        client.post("/api/events", json={
            "event_type": "pothole",
            "confidence": 0.85,
            "severity": "medium",
            "bus_id": "BUS_021",
            "latitude": 28.56390,
            "longitude": 77.20900,
        })
        client.post("/api/events", json={
            "event_type": "pothole",
            "confidence": 0.88,
            "severity": "high",
            "bus_id": "BUS_014",
            "latitude": 28.56392,
            "longitude": 77.20902,
        })
        resp = client.get("/api/hotspots?min_reports=2")
        assert resp.status_code == 200
        hotspots = resp.json()
        assert len(hotspots) >= 1
        hs = hotspots[0]
        # Frontend fields
        assert "center_lat" in hs
        assert "center_lng" in hs
        assert "detection_count" in hs
        assert "priority_score" in hs
        # Integration contract fields
        assert "latitude" in hs
        assert "longitude" in hs
        assert hs["report_count"] == hs["detection_count"]
        assert "max_severity" in hs
        assert len(hs["event_ids"]) >= 2

    def test_root_endpoint_includes_events_stored(self):
        """Verify GET / returns events_stored."""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "events_stored" in data
