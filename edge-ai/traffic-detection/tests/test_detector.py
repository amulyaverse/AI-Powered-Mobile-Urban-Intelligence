"""
tests/test_detector.py
-----------------------
Unit tests for VehicleDetector.

Run with:
    cd edge-ai/traffic-detection
    python -m pytest tests/ -v
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from detector import VehicleDetector, Detection
from config import COCO_VEHICLE_CLASSES


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def detector():
    """Load the detector once for all tests in this module."""
    return VehicleDetector(model_name="yolov8n")


@pytest.fixture
def blank_frame():
    """A blank 640×480 BGR frame (simulates a real frame)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def white_frame():
    return np.ones((720, 1280, 3), dtype=np.uint8) * 255


# ─── Tests ───────────────────────────────────────────────────────────────────

def test_detector_loads(detector):
    """Detector should initialise without errors."""
    assert detector is not None
    assert detector.model is not None


def test_detect_returns_list(detector, blank_frame):
    """detect() always returns a list (even on a blank frame)."""
    result = detector.detect(blank_frame)
    assert isinstance(result, list)


def test_blank_frame_has_no_detections(detector, blank_frame):
    """A pure-black frame should yield zero vehicle detections."""
    result = detector.detect(blank_frame)
    assert result == [], f"Expected no detections on blank frame, got {result}"


def test_detection_fields():
    """Detection dataclass fields and derived properties work correctly."""
    det = Detection(bbox=(10, 20, 110, 120), class_name="car", confidence=0.9, coco_id=2)
    assert det.centroid == (60, 70)
    assert det.area == 100 * 100
    assert det.to_array().shape == (5,)
    assert det.to_xywh() == (10, 20, 100, 100)


def test_detection_to_array():
    det = Detection(bbox=(0, 0, 50, 50), class_name="bus", confidence=0.75, coco_id=5)
    arr = det.to_array()
    assert arr[0] == 0 and arr[1] == 0 and arr[2] == 50 and arr[3] == 50
    assert arr[4] == pytest.approx(0.75)


def test_only_vehicle_classes_in_output(detector, blank_frame):
    """All returned detections must have a class from COCO_VEHICLE_CLASSES."""
    valid_names = set(COCO_VEHICLE_CLASSES.values())
    for det in detector.detect(blank_frame):
        assert det.class_name in valid_names, (
            f"Unexpected class {det.class_name!r} in output"
        )


def test_mean_confidence_empty(detector):
    assert detector.mean_confidence([]) == 0.0


def test_mean_confidence_single():
    detector = VehicleDetector.__new__(VehicleDetector)
    d = Detection(bbox=(0,0,10,10), class_name="car", confidence=0.8, coco_id=2)
    from detector import VehicleDetector as VD
    det = VD.__new__(VD)
    assert VD.mean_confidence(det, [d]) == pytest.approx(0.8)


def test_frame_coverage_empty(detector, blank_frame):
    h, w = blank_frame.shape[:2]
    ratio = detector.frame_coverage([], h, w)
    assert ratio == 0.0


def test_frame_coverage_full():
    """Single detection covering the entire frame → ratio ≈ 1.0."""
    from detector import VehicleDetector as VD
    det = VD.__new__(VD)
    d = Detection(bbox=(0, 0, 640, 480), class_name="car", confidence=0.9, coco_id=2)
    ratio = VD.frame_coverage(det, [d], 480, 640)
    assert ratio == pytest.approx(1.0, abs=0.01)
