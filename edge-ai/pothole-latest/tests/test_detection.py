"""Tests for detection logic — mocked YOLO inference, clustering, severity."""
import pytest
from pothole_pipeline import HealingManager, validate_gps, haversine
from pothole_severity import cluster_boxes, determine_severity_cluster


class TestClusterBoxes:
    """Bounding-box clustering must merge nearby boxes."""

    def test_empty_input(self):
        assert cluster_boxes([]) == []

    def test_single_box(self):
        boxes = [{'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'conf': 0.8, 'class_name': 'Pothole'}]
        clusters = cluster_boxes(boxes)
        assert len(clusters) == 1
        assert clusters[0]['count'] == 1

    def test_two_far_apart_boxes(self):
        boxes = [
            {'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'conf': 0.8, 'class_name': 'Pothole'},
            {'x1': 500, 'y1': 500, 'x2': 550, 'y2': 550, 'conf': 0.7, 'class_name': 'Pothole'},
        ]
        clusters = cluster_boxes(boxes, distance_threshold=60)
        assert len(clusters) == 2

    def test_two_overlapping_boxes_merge(self):
        boxes = [
            {'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'conf': 0.8, 'class_name': 'Pothole'},
            {'x1': 30, 'y1': 30, 'x2': 70, 'y2': 70, 'conf': 0.9, 'class_name': 'Pothole'},
        ]
        clusters = cluster_boxes(boxes, distance_threshold=60)
        assert len(clusters) == 1
        assert clusters[0]['count'] == 2
        assert clusters[0]['conf'] == 0.9  # max confidence kept

    def test_multiple_detections(self):
        boxes = [
            {'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50, 'conf': 0.6, 'class_name': 'Pothole'},
            {'x1': 20, 'y1': 20, 'x2': 60, 'y2': 60, 'conf': 0.7, 'class_name': 'Pothole'},
            {'x1': 400, 'y1': 400, 'x2': 450, 'y2': 450, 'conf': 0.8, 'class_name': 'Pothole'},
        ]
        clusters = cluster_boxes(boxes, distance_threshold=60)
        assert len(clusters) == 2


class TestSeverity:
    """Severity classification must be consistent with documented thresholds."""

    def test_low_severity(self):
        result = determine_severity_cluster(50, 2500, 1920, 1920*1080, 1)
        assert result == "LOW"

    def test_medium_severity(self):
        result = determine_severity_cluster(250, 50000, 1920, 1920*1080, 1)
        assert result == "MEDIUM"

    def test_high_severity(self):
        result = determine_severity_cluster(500, 200000, 1920, 1920*1080, 1)
        assert result == "HIGH"

    def test_very_high_by_width(self):
        result = determine_severity_cluster(800, 50000, 1920, 1920*1080, 1)
        assert result == "VERY HIGH"

    def test_very_high_by_count(self):
        result = determine_severity_cluster(100, 5000, 1920, 1920*1080, 3)
        assert result == "VERY HIGH"

    def test_zero_frame_dimensions(self):
        """Should not crash on zero dimensions."""
        result = determine_severity_cluster(0, 0, 0, 0, 1)
        assert isinstance(result, str)


class TestHaversine:
    """Haversine distance must be accurate for known values."""

    def test_same_point_is_zero(self):
        assert haversine(28.6139, 77.2090, 28.6139, 77.2090) == pytest.approx(0.0, abs=0.01)

    def test_known_distance(self):
        # ~1.1 km between these two Delhi landmarks
        d = haversine(28.6139, 77.2090, 28.6240, 77.2090)
        assert 1000 < d < 1200

    def test_antipodal_points(self):
        d = haversine(0, 0, 0, 180)
        assert d == pytest.approx(20015086, rel=0.01)
