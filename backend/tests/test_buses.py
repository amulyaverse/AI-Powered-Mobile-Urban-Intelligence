"""
tests/test_buses.py
-------------------
Unit tests for Bus fleet management CRUD endpoints.
"""

import pytest
from app.main import app
from app.database import Base, get_db
from app.models.bus import Bus
from app.models.event import Event
from tests.test_events import client, engine, TestingSessionLocal, override_get_db
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)


class TestBusCRUD:
    def test_list_buses_empty(self):
        res = client.get("/api/buses")
        assert res.status_code == 200
        assert res.json() == []

    def test_create_bus_success(self):
        payload = {
            "id": "BUS_100",
            "route": "Route 100",
            "status": "Active",
            "camera_status": "Active",
        }
        res = client.post("/api/buses", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == "BUS_100"
        assert data["route"] == "Route 100"
        assert data["status"] == "Active"
        assert data["camera_status"] == "Active"
        assert "created_at" in data

    def test_create_bus_duplicate_returns_409(self):
        payload = {"id": "BUS_101", "route": "Route 101"}
        res1 = client.post("/api/buses", json=payload)
        assert res1.status_code == 201

        res2 = client.post("/api/buses", json=payload)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"]

    def test_create_bus_invalid_status_returns_422(self):
        payload = {"id": "BUS_102", "status": "InvalidStatus"}
        res = client.post("/api/buses", json=payload)
        assert res.status_code == 422

    def test_get_bus_by_id(self):
        client.post("/api/buses", json={"id": "BUS_103", "route": "Route 103"})
        res = client.get("/api/buses/BUS_103")
        assert res.status_code == 200
        assert res.json()["id"] == "BUS_103"

    def test_get_bus_not_found(self):
        res = client.get("/api/buses/NON_EXISTENT")
        assert res.status_code == 404

    def test_update_bus_patch(self):
        client.post("/api/buses", json={"id": "BUS_104", "route": "Old Route", "status": "Active"})
        res = client.patch("/api/buses/BUS_104", json={"route": "New Route", "status": "Maintenance"})
        assert res.status_code == 200
        data = res.json()
        assert data["route"] == "New Route"
        assert data["status"] == "Maintenance"
        assert data["camera_status"] == "Active"  # unchanged

    def test_update_bus_not_found(self):
        res = client.patch("/api/buses/NON_EXISTENT", json={"route": "Route 99"})
        assert res.status_code == 404

    def test_delete_bus_success(self):
        client.post("/api/buses", json={"id": "BUS_105", "route": "Route 105"})
        res = client.delete("/api/buses/BUS_105")
        assert res.status_code == 204

        # Confirm deleted
        res_get = client.get("/api/buses/BUS_105")
        assert res_get.status_code == 404

    def test_delete_bus_with_events_returns_409(self):
        # Create bus
        client.post("/api/buses", json={"id": "BUS_106", "route": "Route 106"})
        
        # Link an event directly via DB
        db = TestingSessionLocal()
        event = Event(
            event_id="EVT_BUS_TEST",
            event_type="pothole",
            confidence=0.9,
            severity="medium",
            bus_id="BUS_106",
            camera_id="CAM_FRONT",
            latitude=28.56,
            longitude=77.20,
            timestamp=datetime.now(timezone.utc),
            status="new"
        )
        db.add(event)
        db.commit()
        db.close()

        # Attempt to delete bus with linked events
        res = client.delete("/api/buses/BUS_106")
        assert res.status_code == 409
        assert "Cannot delete bus" in res.json()["detail"]
