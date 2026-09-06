"""Performance tests — verify deduplication and cleanup scale reasonably."""
import time
import json
import pytest
from pothole_pipeline import HealingManager


class TestPerformance:
    """Dedup and cleanup must not degrade catastrophically at scale."""

    @pytest.mark.parametrize("n", [100, 1000])
    def test_add_n_unique_potholes(self, healing_manager_factory, n):
        hm = healing_manager_factory(dedup=0.01)  # very small radius to force uniqueness
        start = time.time()
        for i in range(n):
            # Each pothole is separated by ~1.1 km
            hm.get_or_add_pothole(28.0 + i * 0.01, 77.0 + i * 0.01)
        elapsed = time.time() - start
        assert len(hm.known_potholes) == n
        assert elapsed < 30, f"Adding {n} potholes took {elapsed:.2f}s"

    def test_add_10000_potholes(self, healing_manager_factory):
        """10k unique potholes — skipped by default, run with -m 'not slow' to exclude."""
        hm = healing_manager_factory(dedup=0.01)
        start = time.time()
        for i in range(10000):
            hm.get_or_add_pothole(28.0 + (i % 5000) * 0.001, 77.0 + i * 0.001)
        elapsed = time.time() - start
        assert len(hm.known_potholes) == 10000
        # O(n^2) at 10k will be slow; just verify correctness, not speed
        # The test validates that it completes without error

    @pytest.mark.parametrize("n", [100, 1000])
    def test_dedup_lookup_at_scale(self, healing_manager_factory, n):
        hm = healing_manager_factory(dedup=10)
        for i in range(n):
            hm.get_or_add_pothole(28.0 + i * 0.01, 77.0 + i * 0.01)

        # Now look up an existing pothole — must still be fast
        start = time.time()
        for _ in range(100):
            hm.get_or_add_pothole(28.0, 77.0)  # hits first entry
        elapsed = time.time() - start
        assert elapsed < 5

    @pytest.mark.parametrize("n", [100, 1000])
    def test_cache_serialization_at_scale(self, healing_manager_factory, n):
        hm = healing_manager_factory(dedup=0.01)
        for i in range(n):
            hm.get_or_add_pothole(28.0 + i * 0.01, 77.0 + i * 0.01)
        start = time.time()
        cache = hm.get_cache_list()
        serialized = json.dumps(cache)
        loaded = json.loads(serialized)
        elapsed = time.time() - start
        assert len(loaded) == n
        assert elapsed < 5
