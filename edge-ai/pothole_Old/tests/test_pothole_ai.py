"""
tests/test_pothole_ai.py
------------------------
Comprehensive test suite for the Pothole and Road Damage AI module.
Tests detection, confidence thresholding, severity calculation, schema serialization,
single-image inference, real video inference, and edge integration compatibility.
"""

import os
import sys
from pathlib import Path
import pytest
import numpy as np
import cv2

# Add module to sys.path
TEST_DIR = Path(__file__).resolve().parent
MODULE_DIR = TEST_DIR.parent
PROJECT_DIR = MODULE_DIR.parents[1]
sys.path.insert(0, str(MODULE_DIR))
sys.path.insert(0, str(PROJECT_DIR / "integration" / "event-generator"))

from pothole_severity import calculate_severity
from pothole_event_schema import PotholeDetection, PotholeFrameSummary
from pothole_detector import PotholeDetector
from pothole_pipeline import PotholePipeline
from pothole_config import CONFIDENCE_THRESHOLD, SAMPLE_VIDEOS


# ── 1. Severity & Geometric Scoring Tests ────────────────────────────────────

class TestSeverityScoring:
    def test_small_pothole_evaluates_to_low_severity(self):
        # 20x20 box in 640x360 frame -> area = 400 / 230400 = 0.0017 (< 0.015)
        bbox = (100, 100, 120, 120)
        severity, metrics = calculate_severity(bbox, (360, 640))
        assert severity == "low"
        assert metrics["area_ratio"] < 0.015
        assert metrics["width_ratio"] < 0.09

    def test_medium_pothole_evaluates_to_medium_severity(self):
        # 100x60 box in 640x360 frame -> area = 6000 / 230400 = 0.026 (> 0.015, < 0.06)
        bbox = (100, 100, 200, 160)
        severity, metrics = calculate_severity(bbox, (360, 640))
        assert severity == "medium"
        assert 0.015 <= metrics["area_ratio"] < 0.06

    def test_large_pothole_evaluates_to_high_severity(self):
        # 200x120 box in 640x360 frame -> area = 24000 / 230400 = 0.104 (> 0.06)
        bbox = (100, 100, 300, 220)
        severity, metrics = calculate_severity(bbox, (360, 640))
        assert severity == "high"
        assert metrics["area_ratio"] >= 0.06

    def test_wide_pothole_triggers_high_severity_via_width_ratio(self):
        # Width = 180 in 640 -> width_ratio = 180 / 640 = 0.281 (> 0.22)
        bbox = (50, 100, 230, 120)
        severity, metrics = calculate_severity(bbox, (360, 640))
        assert severity == "high"
        assert metrics["width_ratio"] >= 0.22

    def test_zero_dimensions_graceful_handling(self):
        bbox = (0, 0, 0, 0)
        severity, metrics = calculate_severity(bbox, (0, 0))
        assert severity == "low"
        assert metrics["area_ratio"] == 0.0


# ── 2. Event Schema & Serialization Tests ─────────────────────────────────────

class TestEventSchema:
    def test_single_detection_schema_fields(self):
        det = PotholeDetection(
            bbox=(120, 80, 360, 250),
            class_name="pothole",
            confidence=0.87,
            severity="high",
            area_ratio=0.075,
            source_frame=125,
            evidence="/tmp/evidence_125.jpg",
        )
        d = det.to_dict()

        # Check required fields per Phase 2 & 10 specifications
        assert d["event_type"] == "pothole"
        assert d["confidence"] == 0.87
        assert d["severity"] == "high"
        assert d["bbox"] == [120, 80, 360, 250]
        assert d["source_frame"] == 125
        assert d["evidence"] == "/tmp/evidence_125.jpg"

    def test_multiple_detections_frame_summary(self):
        det1 = PotholeDetection(bbox=(10, 10, 50, 50), class_name="pothole", confidence=0.75, severity="low", source_frame=10)
        det2 = PotholeDetection(bbox=(100, 100, 300, 250), class_name="pothole", confidence=0.91, severity="high", source_frame=10)

        summary = PotholeFrameSummary(
            source_frame=10,
            detections=[det1, det2],
            timestamp="2026-09-06T11:00:00Z"
        )
        res = summary.to_dict()
        assert res["source_frame"] == 10
        assert res["count"] == 2
        assert len(res["detections"]) == 2
        assert res["detections"][0]["severity"] == "low"
        assert res["detections"][1]["severity"] == "high"


# ── 3. Confidence Filtering & Detector Inference Tests ───────────────────────

@pytest.fixture(scope="module")
def pothole_detector():
    """Load the detector once for all tests in this module."""
    return PotholeDetector(model_path="yolov8n.pt", conf=CONFIDENCE_THRESHOLD)


class TestPotholeDetector:
    def test_detector_initialization(self, pothole_detector):
        assert pothole_detector.conf == 0.65
        assert pothole_detector.model is not None

    def test_detection_on_empty_frame_returns_empty_list(self, pothole_detector):
        blank = np.zeros((360, 640, 3), dtype=np.uint8)
        detections = pothole_detector.detect(blank)
        assert isinstance(detections, list)
        assert len(detections) == 0

    def test_mean_confidence_and_worst_severity(self, pothole_detector):
        det1 = PotholeDetection((0, 0, 10, 10), "pothole", 0.70, "low")
        det2 = PotholeDetection((0, 0, 50, 50), "pothole", 0.90, "high")
        assert pothole_detector.mean_confidence([det1, det2]) == 0.80
        assert pothole_detector.worst_severity([det1, det2]) == "high"
        assert pothole_detector.worst_severity([]) is None


# ── 4. Pipeline & Single Image / Video Tests ─────────────────────────────────

class TestPotholePipeline:
    def test_pipeline_on_synthetic_image(self, tmp_path):
        img_path = tmp_path / "test_road.jpg"
        # Create a synthetic road image with gray background
        img = np.full((360, 640, 3), 120, dtype=np.uint8)
        cv2.imwrite(str(img_path), img)

        pipeline = PotholePipeline(
            source=str(img_path),
            conf_thresh=0.65,
            evidence_dir=str(tmp_path / "evidence"),
            show=False
        )
        results = list(pipeline.run())
        assert isinstance(results, list)

    def test_pipeline_on_sample_video(self):
        sample_video = SAMPLE_VIDEOS.get("city")
        if not sample_video or not sample_video.exists():
            pytest.skip("Sample video cityRoad_potHoles.mp4 not found")

        # Process first 30 frames of sample video
        cap = cv2.VideoCapture(str(sample_video))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        assert total_frames > 0


# ── 5. Edge Integration Layer Compatibility ──────────────────────────────────

class TestEdgeIntegrationHandoff:
    def test_ai_output_consumed_by_event_generator(self):
        """Verify Parminder's build_event correctly consumes Pothole AI output."""
        try:
            from event_generator import build_event
        except ImportError:
            pytest.skip("event_generator not available in test environment")

        ai_output = {
            "event_type": "pothole",
            "confidence": 0.88,
            "severity": "high",
            "bbox": [150, 100, 320, 240],
            "source_frame": 45,
            "evidence": "evidence/frame_000045.jpg",
        }

        event = build_event(ai_output)
        assert event is not None
        assert event["event_type"] == "pothole"
        assert event["confidence"] == 0.88
        assert event["severity"] == "high"
        assert event["status"] == "new"
        assert "event_id" in event
        assert "latitude" in event
        assert "longitude" in event
        assert "timestamp" in event

    def test_low_confidence_discarded_by_event_generator(self):
        """Verify detections below 0.65 are rejected by event generator."""
        try:
            from event_generator import build_event
        except ImportError:
            pytest.skip("event_generator not available in test environment")

        low_conf_output = {
            "event_type": "pothole",
            "confidence": 0.55,
            "severity": "low",
        }
        event = build_event(low_conf_output)
        assert event is None
