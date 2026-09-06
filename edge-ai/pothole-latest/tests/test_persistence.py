"""Tests for JSON persistence safety."""
import json
import os
import pytest
from pothole_pipeline import HealingManager


class TestCachePersistence:
    """Known-potholes cache must survive serialization round-trips."""

    def test_save_and_reload(self, healing_manager_factory, tmp_path):
        hm1 = healing_manager_factory()
        hm1.get_or_add_pothole(28.6139, 77.2090)
        hm1.get_or_add_pothole(28.6200, 77.2200)
        cache = hm1.get_cache_list()

        fp = tmp_path / "cache.json"
        fp.write_text(json.dumps(cache, indent=2))

        loaded = json.loads(fp.read_text())
        hm2 = healing_manager_factory(potholes=loaded)

        assert len(hm2.known_potholes) == 2
        for entry in cache:
            assert entry["event_id"] in hm2.known_potholes

    def test_ids_preserved_across_restart(self, healing_manager_factory, tmp_path):
        hm1 = healing_manager_factory()
        pid = hm1.get_or_add_pothole(28.6139, 77.2090)
        cache = hm1.get_cache_list()

        fp = tmp_path / "cache.json"
        fp.write_text(json.dumps(cache))
        loaded = json.loads(fp.read_text())

        hm2 = healing_manager_factory(potholes=loaded)
        assert pid in hm2.known_potholes

    def test_cache_output_has_required_fields(self, healing_manager_factory):
        hm = healing_manager_factory()
        hm.get_or_add_pothole(28.6139, 77.2090)
        cache = hm.get_cache_list()
        entry = cache[0]
        assert "event_id" in entry
        assert "latitude" in entry
        assert "longitude" in entry

    def test_empty_cache_produces_empty_list(self, healing_manager_factory):
        hm = healing_manager_factory()
        assert hm.get_cache_list() == []


class TestMalformedJSON:
    """Malformed persistent files must NOT silently destroy data."""

    def test_duplicate_ids_raise_error(self, healing_manager_factory):
        dups = [
            {"event_id": "DUP", "latitude": 28.6139, "longitude": 77.2090},
            {"event_id": "DUP", "latitude": 28.6200, "longitude": 77.2200},
        ]
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            healing_manager_factory(potholes=dups)

    def test_invalid_gps_records_skipped(self, healing_manager_factory):
        records = [
            {"event_id": "good", "latitude": 28.6139, "longitude": 77.2090},
            {"event_id": "bad",  "latitude": None,    "longitude": None},
        ]
        hm = healing_manager_factory(potholes=records)
        assert "good" in hm.known_potholes
        assert "bad" not in hm.known_potholes

    def test_missing_file_means_empty(self, healing_manager_factory):
        """No file → empty cache, not an error."""
        hm = healing_manager_factory(potholes=[])
        assert len(hm.known_potholes) == 0


class TestAtomicWrite:
    """Atomic write must not leave partial files."""

    def test_atomic_write_pattern(self, tmp_path):
        target = tmp_path / "known_potholes.json"
        data = [{"event_id": "test-1", "latitude": 28.6139, "longitude": 77.2090}]

        tmp_file = str(target) + ".tmp"
        with open(tmp_file, 'w') as f:
            json.dump(data, f, indent=4)
        os.replace(tmp_file, str(target))

        loaded = json.loads(target.read_text())
        assert loaded[0]["event_id"] == "test-1"
        assert not os.path.exists(tmp_file)
