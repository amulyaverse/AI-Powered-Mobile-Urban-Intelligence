"""Tests for event_id generation, persistence, and uniqueness."""
import json
import pytest
from pothole_pipeline import HealingManager, validate_gps


class TestEventIdGeneration:
    """event_id must be generated once for a new pothole and reused for the same location."""

    def test_new_pothole_gets_event_id(self, healing_manager_factory):
        hm = healing_manager_factory()
        pid = hm.get_or_add_pothole(28.6139, 77.2090)
        assert pid  # non-empty
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_same_location_returns_same_id(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.6139, 77.2090)
        pid2 = hm.get_or_add_pothole(28.6139, 77.2090)
        assert pid1 == pid2

    def test_nearby_location_returns_same_id(self, healing_manager_factory):
        """Two detections within dedup radius must share the same ID."""
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.613900, 77.209000)
        pid2 = hm.get_or_add_pothole(28.613905, 77.209005)
        assert pid1 == pid2

    def test_distant_locations_get_different_ids(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.6139, 77.2090)
        pid2 = hm.get_or_add_pothole(28.6200, 77.2200)
        assert pid1 != pid2

    def test_event_id_unique_across_potholes(self, healing_manager_factory):
        """Multiple far-apart potholes must each get a unique ID."""
        hm = healing_manager_factory(dedup=5)
        ids = set()
        for i in range(20):
            pid = hm.get_or_add_pothole(28.0 + i * 0.01, 77.0 + i * 0.01)
            ids.add(pid)
        assert len(ids) == 20


class TestEventIdSerialization:
    """event_id must survive JSON round-trip and cache reload."""

    def test_id_survives_json_roundtrip(self, healing_manager_factory):
        hm = healing_manager_factory()
        pid = hm.get_or_add_pothole(28.6139, 77.2090)
        cache = hm.get_cache_list()
        serialized = json.dumps(cache)
        loaded = json.loads(serialized)
        assert loaded[0]["event_id"] == pid

    def test_id_survives_reload(self, healing_manager_factory):
        """Simulate restart: create → serialize → reload → check ID."""
        hm1 = healing_manager_factory()
        pid_original = hm1.get_or_add_pothole(28.6139, 77.2090)
        cache = hm1.get_cache_list()

        hm2 = healing_manager_factory(potholes=cache)
        assert pid_original in hm2.known_potholes

    def test_legacy_id_field_migrated(self, healing_manager_factory):
        """Legacy records with 'id' (not 'event_id') must be loaded correctly."""
        legacy = [{"id": "legacy-123", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=legacy)
        assert "legacy-123" in hm.known_potholes

    def test_event_id_preferred_over_legacy_id(self, healing_manager_factory):
        """If both 'event_id' and 'id' exist, 'event_id' takes precedence."""
        record = [{"event_id": "new-456", "id": "old-789", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=record)
        assert "new-456" in hm.known_potholes
        assert "old-789" not in hm.known_potholes

    def test_cache_output_uses_event_id_key(self, healing_manager_factory):
        hm = healing_manager_factory()
        hm.get_or_add_pothole(28.6139, 77.2090)
        cache = hm.get_cache_list()
        assert "event_id" in cache[0]
        assert cache[0]["event_id"]  # non-empty
