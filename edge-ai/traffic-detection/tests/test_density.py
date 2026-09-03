"""
tests/test_density.py
---------------------
Unit tests for DensityEstimator and TrafficEvent schema.

Run with:
    cd edge-ai/traffic-detection
    python -m pytest tests/ -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from density_estimator import DensityEstimator, DensityResult
from event_schema import TrafficEvent, GPSCoordinate


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def estimator():
    return DensityEstimator()


# ─── DensityEstimator tests ───────────────────────────────────────────────────

class TestDensityEstimator:

    def test_low_density(self, estimator):
        result = estimator.estimate(in_frame_count=2)
        assert result.label == "LOW"
        assert 0.0 <= result.score <= 1.0

    def test_medium_density(self, estimator):
        result = estimator.estimate(in_frame_count=9)
        assert result.label == "MEDIUM"

    def test_high_density(self, estimator):
        result = estimator.estimate(in_frame_count=16)
        assert result.label == "HIGH"

    def test_critical_density(self, estimator):
        result = estimator.estimate(in_frame_count=25)
        assert result.label == "CRITICAL"

    def test_zero_vehicles(self, estimator):
        result = estimator.estimate(in_frame_count=0, frame_coverage_ratio=0.0)
        assert result.label == "LOW"
        assert result.score == pytest.approx(0.0, abs=0.01)

    def test_score_increases_with_count(self, estimator):
        r_low  = estimator.estimate(3)
        r_high = estimator.estimate(20)
        assert r_low.score < r_high.score

    def test_coverage_affects_score(self, estimator):
        r_no_coverage   = estimator.estimate(10, frame_coverage_ratio=0.0)
        r_high_coverage = estimator.estimate(10, frame_coverage_ratio=0.8)
        assert r_high_coverage.score > r_no_coverage.score

    def test_result_is_dataclass(self, estimator):
        result = estimator.estimate(5)
        assert isinstance(result, DensityResult)
        assert hasattr(result, "label")
        assert hasattr(result, "score")
        assert hasattr(result, "in_frame_count")
        assert hasattr(result, "coverage_ratio")

    def test_boundary_low_medium(self, estimator):
        """Count = 5 → LOW. Count = 6 → MEDIUM."""
        assert estimator.estimate(5).label  == "LOW"
        assert estimator.estimate(6).label  == "MEDIUM"

    def test_boundary_medium_high(self, estimator):
        assert estimator.estimate(12).label == "MEDIUM"
        assert estimator.estimate(13).label == "HIGH"

    def test_boundary_high_critical(self, estimator):
        assert estimator.estimate(20).label == "HIGH"
        assert estimator.estimate(21).label == "CRITICAL"

    def test_large_count_clipped(self, estimator):
        """A very large count should not produce score > 1."""
        result = estimator.estimate(1000, frame_coverage_ratio=1.0)
        assert result.score <= 1.0


# ─── TrafficEvent tests ───────────────────────────────────────────────────────

class TestTrafficEvent:

    def test_default_event(self):
        event = TrafficEvent()
        assert event.event_type == "traffic_snapshot"
        assert event.density == "LOW"
        assert event.total_vehicles == 0

    def test_summary_format(self):
        event = TrafficEvent(
            vehicle_counts={"car": 18, "bike": 9, "bus": 2, "truck": 3},
            total_vehicles=32,
            density="HIGH",
            confidence=0.87,
        )
        s = event.summary()
        assert "18" in s
        assert "HIGH" in s
        assert "0.87" in s

    def test_to_dict(self):
        event = TrafficEvent(bus_id="BUS-042")
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d["bus_id"] == "BUS-042"
        assert "gps" in d
        assert isinstance(d["gps"], dict)

    def test_to_json_is_valid(self):
        import json
        event = TrafficEvent()
        j = event.to_json()
        parsed = json.loads(j)
        assert parsed["event_type"] == "traffic_snapshot"

    def test_gps_coordinate(self):
        gps = GPSCoordinate(lat=12.9716, lon=77.5946)
        assert gps.lat == pytest.approx(12.9716)
        d = gps.to_dict()
        assert d["lat"] == pytest.approx(12.9716)
        assert d["lon"] == pytest.approx(77.5946)

    def test_timestamp_iso_auto_set(self):
        event = TrafficEvent()
        assert len(event.timestamp_iso) > 0
        assert "T" in event.timestamp_iso  # ISO format check
