"""Tests for GPS-based deduplication."""
import pytest
from pothole_pipeline import HealingManager, haversine
from pothole_config import DEDUPLICATION_RADIUS_METERS


class TestDeduplication:
    """Potholes within dedup radius must share an ID; outside must differ."""

    def test_exact_same_location(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.6139, 77.2090)
        pid2 = hm.get_or_add_pothole(28.6139, 77.2090)
        assert pid1 == pid2
        assert len(hm.known_potholes) == 1

    def test_within_radius(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.613900, 77.209000)
        pid2 = hm.get_or_add_pothole(28.613905, 77.209005)
        pid3 = hm.get_or_add_pothole(28.613910, 77.209010)
        assert pid1 == pid2 == pid3
        assert len(hm.known_potholes) == 1

    def test_outside_radius(self, healing_manager_factory):
        hm = healing_manager_factory(dedup=10)
        pid1 = hm.get_or_add_pothole(28.6139, 77.2090)
        pid2 = hm.get_or_add_pothole(28.6200, 77.2200)
        assert pid1 != pid2
        assert len(hm.known_potholes) == 2

    def test_configurable_radius(self, healing_manager_factory):
        """Two points ~5m apart: within 10m radius → same; within 1m radius → different."""
        lat1, lon1 = 28.613900, 77.209000
        lat2, lon2 = 28.613945, 77.209000  # ~5m north

        hm_wide = healing_manager_factory(dedup=10)
        assert hm_wide.get_or_add_pothole(lat1, lon1) == hm_wide.get_or_add_pothole(lat2, lon2)

        hm_narrow = healing_manager_factory(dedup=1)
        assert hm_narrow.get_or_add_pothole(lat1, lon1) != hm_narrow.get_or_add_pothole(lat2, lon2)

    def test_dedup_radius_uses_haversine(self, healing_manager_factory):
        """Distance must use geographic (haversine) distance, not coordinate diff."""
        hm = healing_manager_factory(dedup=5)
        pid1 = hm.get_or_add_pothole(28.6139, 77.2090)
        # ~1.1m away — well within 5m
        pid2 = hm.get_or_add_pothole(28.61391, 77.2090)
        assert pid1 == pid2

    def test_default_dedup_radius_from_config(self):
        """The config default must be a positive number."""
        assert DEDUPLICATION_RADIUS_METERS > 0

    def test_no_duplicate_cache_entries(self, healing_manager_factory):
        """Adding the same pothole 100 times must not grow the cache."""
        hm = healing_manager_factory(dedup=10)
        for _ in range(100):
            hm.get_or_add_pothole(28.6139, 77.2090)
        assert len(hm.known_potholes) == 1
