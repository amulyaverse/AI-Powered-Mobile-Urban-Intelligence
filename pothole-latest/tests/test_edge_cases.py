"""Edge-case tests for boundary conditions and unusual inputs."""
import json
import math
import pytest
from pothole_pipeline import HealingManager, validate_gps, haversine


class TestEdgeCaseGPS:
    """GPS edge cases: poles, dateline, tiny offsets."""

    def test_pothole_at_north_pole(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid = hm.get_or_add_pothole(90.0, 0.0)
        assert pid

    def test_pothole_at_south_pole(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid = hm.get_or_add_pothole(-90.0, 0.0)
        assert pid

    def test_pothole_at_dateline(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid = hm.get_or_add_pothole(0.0, 180.0)
        assert pid

    def test_pothole_at_antimeridian(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid = hm.get_or_add_pothole(0.0, -180.0)
        assert pid


class TestEdgeCaseHealing:
    """Healing edge cases."""

    def test_healing_exactly_at_threshold(self, healing_manager_factory):
        """Exactly frame_confidence empty frames triggers resolution."""
        records = [{"event_id": "P", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=5)
        resolved = []
        for i in range(5):
            resolved.extend(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert len(resolved) == 1

    def test_healing_one_frame_short(self, healing_manager_factory):
        """frame_confidence - 1 empty frames must NOT trigger resolution."""
        records = [{"event_id": "P", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=5)
        resolved = []
        for _ in range(4):
            resolved.extend(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert len(resolved) == 0
        assert "P" in hm.known_potholes

    def test_empty_known_potholes_list(self, healing_manager_factory):
        """Empty initial cache must not crash."""
        hm = healing_manager_factory(potholes=[])
        assert len(hm.known_potholes) == 0

    def test_process_frame_with_empty_cache(self, healing_manager_factory):
        """Processing frames with no known potholes must not crash."""
        hm = healing_manager_factory(potholes=[])
        resolved = list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert resolved == []

    def test_healing_far_from_any_pothole(self, healing_manager_factory):
        records = [{"event_id": "P", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=2)
        for _ in range(100):
            resolved = list(hm.process_frame(0.0, 0.0, potholes_detected=False))
            assert len(resolved) == 0
        assert "P" in hm.known_potholes


class TestEdgeCaseSerialization:
    """Serialization edge cases."""

    def test_large_cache_roundtrip(self, healing_manager_factory, tmp_path):
        hm = healing_manager_factory(dedup=0.1)
        for i in range(50):
            hm.get_or_add_pothole(28.0 + i * 0.01, 77.0 + i * 0.01)
        cache = hm.get_cache_list()
        fp = tmp_path / "big.json"
        fp.write_text(json.dumps(cache))
        loaded = json.loads(fp.read_text())
        assert len(loaded) == 50

    def test_special_characters_in_legacy_id(self, healing_manager_factory):
        """Legacy IDs with special chars must survive."""
        records = [{"id": "pothole/city#1", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records)
        assert "pothole/city#1" in hm.known_potholes
        cache = hm.get_cache_list()
        serialized = json.dumps(cache)
        reloaded = json.loads(serialized)
        assert reloaded[0]["event_id"] == "pothole/city#1"
