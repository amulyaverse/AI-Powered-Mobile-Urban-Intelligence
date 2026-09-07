"""End-to-end lifecycle tests — detect, persist, re-detect, heal, redetect."""
import json
import pytest
from pothole_pipeline import HealingManager


class TestFullLifecycle:
    """Simulate the complete pothole lifecycle through the HealingManager."""

    def test_detect_persist_redetect_heal(self, healing_manager_factory, tmp_path):
        """
        Pass 1: detect A, B, C
        Heal B
        Pass 2: re-detect A and C (keep IDs), encounter B location (no new pothole)
        """
        # Pass 1: detect three potholes
        hm = healing_manager_factory(radius=15, frames=3, dedup=10)
        pid_a = hm.get_or_add_pothole(28.6100, 77.2000)
        pid_b = hm.get_or_add_pothole(28.6200, 77.2100)
        pid_c = hm.get_or_add_pothole(28.6300, 77.2200)
        assert len(hm.known_potholes) == 3

        # Persist to disk
        cache1 = hm.get_cache_list()
        fp = tmp_path / "cache.json"
        fp.write_text(json.dumps(cache1))

        # Heal B: 3 empty frames near B
        healed = []
        for _ in range(3):
            healed.extend(hm.process_frame(28.6200, 77.2100, potholes_detected=False))
        assert len(healed) == 1
        healed_pid, _ = healed[0]
        assert healed_pid == pid_b

        # Persist updated cache
        cache2 = hm.get_cache_list()
        fp.write_text(json.dumps(cache2))
        assert len(cache2) == 2

        # Pass 2: reload and simulate
        loaded = json.loads(fp.read_text())
        hm2 = healing_manager_factory(potholes=loaded, radius=15, frames=3, dedup=10)

        # A and C still have original IDs
        assert pid_a in hm2.known_potholes
        assert pid_c in hm2.known_potholes
        assert pid_b not in hm2.known_potholes

        # Re-detect A → same ID
        pid_a2 = hm2.get_or_add_pothole(28.6100, 77.2000)
        assert pid_a2 == pid_a

        # Re-detect C → same ID
        pid_c2 = hm2.get_or_add_pothole(28.6300, 77.2200)
        assert pid_c2 == pid_c

        # Encounter B's location — no detection
        # B must NOT reappear in the cache
        assert pid_b not in hm2.known_potholes

    def test_new_pothole_at_healed_location(self, healing_manager_factory):
        """After healing, a genuine new pothole at the same location gets a new ID."""
        hm = healing_manager_factory(radius=15, frames=2, dedup=5)

        # Detect original pothole
        pid_old = hm.get_or_add_pothole(28.6139, 77.2090)

        # Heal it
        for _ in range(2):
            list(hm.process_frame(28.6139, 77.2090, potholes_detected=False))
        assert pid_old not in hm.known_potholes

        # New pothole genuinely detected at same location
        pid_new = hm.get_or_add_pothole(28.6139, 77.2090)
        assert pid_new != pid_old

    def test_multipass_stability(self, healing_manager_factory, tmp_path):
        """Three full passes with persist/reload between each."""
        fp = tmp_path / "cache.json"

        # Pass 1
        hm = healing_manager_factory(dedup=10, radius=15, frames=2)
        id1 = hm.get_or_add_pothole(28.6139, 77.2090)
        fp.write_text(json.dumps(hm.get_cache_list()))

        # Pass 2 — reload
        loaded = json.loads(fp.read_text())
        hm = healing_manager_factory(potholes=loaded, dedup=10, radius=15, frames=2)
        id2 = hm.get_or_add_pothole(28.6139, 77.2090)
        assert id1 == id2
        fp.write_text(json.dumps(hm.get_cache_list()))

        # Pass 3 — reload again
        loaded = json.loads(fp.read_text())
        hm = healing_manager_factory(potholes=loaded, dedup=10, radius=15, frames=2)
        id3 = hm.get_or_add_pothole(28.6139, 77.2090)
        assert id1 == id3


class TestMultiBus:
    """Multiple buses operating on the same cache."""

    def test_bus_b_sees_bus_a_pothole(self, healing_manager_factory, tmp_path):
        fp = tmp_path / "shared.json"

        # Bus A detects a pothole
        hm_a = healing_manager_factory(dedup=10)
        pid = hm_a.get_or_add_pothole(28.6139, 77.2090)
        fp.write_text(json.dumps(hm_a.get_cache_list()))

        # Bus B loads the same cache
        loaded = json.loads(fp.read_text())
        hm_b = healing_manager_factory(potholes=loaded, dedup=10)
        pid_b = hm_b.get_or_add_pothole(28.6139, 77.2090)

        assert pid == pid_b  # same pothole
