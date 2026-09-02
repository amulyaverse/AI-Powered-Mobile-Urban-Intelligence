"""
tests/test_counter.py
---------------------
Unit tests for VehicleCounter — line-crossing logic.

Run with:
    cd edge-ai/traffic-detection
    python -m pytest tests/ -v
"""

import sys, os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from counter import VehicleCounter
from tracker import TrackedVehicle


def _make_vehicle(track_id: int, cx: int, cy: int, cls: str = "car") -> TrackedVehicle:
    """Helper: create a TrackedVehicle with centroid at (cx, cy)."""
    half = 30
    return TrackedVehicle(
        track_id=track_id,
        bbox=(cx - half, cy - half, cx + half, cy + half),
        class_name=cls,
        confidence=0.9,
    )


@pytest.fixture
def counter():
    """Counter with line at y=200 in a 400×640 frame."""
    return VehicleCounter(frame_height=400, frame_width=640, line_ratio=0.5)
    # line_y = 400 * 0.5 = 200


class TestVehicleCounter:

    def test_line_position(self, counter):
        assert counter.line_y == 200

    def test_no_count_single_frame(self, counter):
        """A vehicle appearing in one frame above the line → not counted yet."""
        v = _make_vehicle(1, cx=320, cy=100)
        counts = counter.update([v])
        assert counts.get("car", 0) == 0

    def test_count_on_crossing_top_to_bottom(self, counter):
        """Vehicle moves from above line (cy=100) to below (cy=300) → counted."""
        v1 = _make_vehicle(1, cx=320, cy=100)
        counter.update([v1])                      # frame 1: above
        v2 = _make_vehicle(1, cx=320, cy=300)
        counts = counter.update([v2])             # frame 2: below → crosses line
        assert counts.get("car", 0) == 1

    def test_count_on_crossing_bottom_to_top(self, counter):
        """Vehicle moves from below line (cy=300) to above (cy=100) → counted."""
        v1 = _make_vehicle(2, cx=320, cy=300)
        counter.update([v1])
        v2 = _make_vehicle(2, cx=320, cy=100)
        counts = counter.update([v2])
        assert counts.get("car", 0) == 1

    def test_no_double_count(self, counter):
        """Vehicle crossing the line multiple times is only counted once."""
        # Cross 1
        counter.update([_make_vehicle(3, cx=320, cy=100)])
        counter.update([_make_vehicle(3, cx=320, cy=300)])
        # Cross back
        counter.update([_make_vehicle(3, cx=320, cy=100)])
        counter.update([_make_vehicle(3, cx=320, cy=300)])
        counts = counter.update([_make_vehicle(3, cx=320, cy=100)])
        assert counts.get("car", 0) == 1, "Vehicle should only be counted once"

    def test_multiple_classes(self, counter):
        """Different classes counted separately."""
        # Car crosses
        counter.update([_make_vehicle(10, cx=100, cy=100, cls="car")])
        counter.update([_make_vehicle(10, cx=100, cy=300, cls="car")])
        # Truck crosses
        counter.update([_make_vehicle(11, cx=200, cy=100, cls="truck")])
        counts = counter.update([_make_vehicle(11, cx=200, cy=300, cls="truck")])
        assert counts.get("car",   0) == 1
        assert counts.get("truck", 0) == 1
        assert counts.get("bike",  0) == 0

    def test_reset_clears_counts(self, counter):
        """reset() zeros all counts."""
        counter.update([_make_vehicle(20, cx=320, cy=100)])
        counter.update([_make_vehicle(20, cx=320, cy=300)])
        counter.reset()
        assert counter.total == 0
        assert counter.counts == {}

    def test_total_property(self, counter):
        counter.update([_make_vehicle(30, cx=320, cy=100, cls="bus")])
        counter.update([_make_vehicle(30, cx=320, cy=300, cls="bus")])
        counter.update([_make_vehicle(31, cx=100, cy=100, cls="bike")])
        counter.update([_make_vehicle(31, cx=100, cy=300, cls="bike")])
        assert counter.total == 2

    def test_draw_line_does_not_crash(self, counter):
        frame = np.zeros((400, 640, 3), dtype=np.uint8)
        result = counter.draw_line(frame)
        assert result.shape == (400, 640, 3)

    def test_draw_tracks_does_not_crash(self, counter):
        frame = np.zeros((400, 640, 3), dtype=np.uint8)
        vehicles = [_make_vehicle(99, cx=320, cy=200)]
        result = counter.draw_tracks(frame, vehicles)
        assert result.shape == (400, 640, 3)
