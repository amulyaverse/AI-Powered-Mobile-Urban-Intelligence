"""Tests for deletion / treatment lifecycle."""
import json
import pytest
from pothole_pipeline import HealingManager


class TestDeletion:
    """Deleting (resolving) a pothole must remove exactly that record."""

    def _make_hm_with_abc(self, healing_manager_factory):
        """Helper: create manager with potholes A, B, C far apart."""
        records = [
            {"event_id": "A", "latitude": 28.6100, "longitude": 77.2000},
            {"event_id": "B", "latitude": 28.6200, "longitude": 77.2100},
            {"event_id": "C", "latitude": 28.6300, "longitude": 77.2200},
        ]
        return healing_manager_factory(potholes=records, radius=15, frames=3)

    def test_delete_middle(self, healing_manager_factory):
        hm = self._make_hm_with_abc(healing_manager_factory)
        # Simulate healing near B (no potholes detected for 3 frames)
        for _ in range(3):
            list(hm.process_frame(28.6200, 77.2100, potholes_detected=False))
        assert "B" not in hm.known_potholes
        assert "A" in hm.known_potholes
        assert "C" in hm.known_potholes

    def test_delete_first(self, healing_manager_factory):
        hm = self._make_hm_with_abc(healing_manager_factory)
        for _ in range(3):
            list(hm.process_frame(28.6100, 77.2000, potholes_detected=False))
        assert "A" not in hm.known_potholes
        assert "B" in hm.known_potholes
        assert "C" in hm.known_potholes

    def test_delete_last(self, healing_manager_factory):
        hm = self._make_hm_with_abc(healing_manager_factory)
        for _ in range(3):
            list(hm.process_frame(28.6300, 77.2200, potholes_detected=False))
        assert "C" not in hm.known_potholes
        assert "A" in hm.known_potholes
        assert "B" in hm.known_potholes

    def test_delete_only_record(self, healing_manager_factory):
        records = [{"event_id": "only", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=2)
        for _ in range(2):
            list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert len(hm.known_potholes) == 0

    def test_nonexistent_location_no_corruption(self, healing_manager_factory):
        hm = self._make_hm_with_abc(healing_manager_factory)
        # Process frame far from any known pothole
        for _ in range(10):
            list(hm.process_frame(10.0, 10.0, potholes_detected=False))
        assert len(hm.known_potholes) == 3

    def test_repeated_deletion_is_safe(self, healing_manager_factory):
        records = [{"event_id": "X", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=2)
        for _ in range(2):
            list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert "X" not in hm.known_potholes
        # Process again at same location — must not crash
        for _ in range(5):
            results = list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert len(hm.known_potholes) == 0

    def test_deletion_preserves_other_ids(self, healing_manager_factory):
        hm = self._make_hm_with_abc(healing_manager_factory)
        id_a_before = "A"
        id_c_before = "C"
        for _ in range(3):
            list(hm.process_frame(28.6200, 77.2100, potholes_detected=False))
        cache = hm.get_cache_list()
        ids = {e["event_id"] for e in cache}
        assert id_a_before in ids
        assert id_c_before in ids

    def test_json_valid_after_deletion(self, healing_manager_factory, tmp_path):
        hm = self._make_hm_with_abc(healing_manager_factory)
        for _ in range(3):
            list(hm.process_frame(28.6200, 77.2100, potholes_detected=False))
        cache = hm.get_cache_list()
        fp = tmp_path / "after_delete.json"
        fp.write_text(json.dumps(cache, indent=2))
        reloaded = json.loads(fp.read_text())
        assert len(reloaded) == 2


class TestHealingLifecycle:
    """Healing must only trigger when the pothole is truly absent."""

    def test_detection_resets_healing_counter(self, healing_manager_factory):
        records = [{"event_id": "P", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=5)
        # 4 empty frames (not enough to heal)
        for _ in range(4):
            list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert "P" in hm.known_potholes
        # Detection resets the counter
        list(hm.process_frame(28.6139, 77.2090, potholes_detected=True))
        # Another 4 empty frames — still not enough
        for _ in range(4):
            list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert "P" in hm.known_potholes

    def test_visible_pothole_not_marked_repaired(self, healing_manager_factory):
        records = [{"event_id": "P", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=3)
        # Continuous detection must never resolve
        for _ in range(100):
            resolved = list(hm.process_frame(28.6139, 77.2090, potholes_detected=True))
            assert len(resolved) == 0
        assert "P" in hm.known_potholes

    def test_resolution_event_contains_correct_id(self, healing_manager_factory):
        records = [{"event_id": "HEAL-ME", "latitude": 28.6139, "longitude": 77.2090}]
        hm = healing_manager_factory(potholes=records, radius=15, frames=2)
        all_resolved = []
        for _ in range(2):
            all_resolved.extend(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert len(all_resolved) == 1
        pid, data = all_resolved[0]
        assert pid == "HEAL-ME"
