"""
config.py
---------
Configuration parameters for the Pothole and Road Damage AI module.
Single source of truth for thresholds, model paths, and class labels.
"""

from pathlib import Path

# ── Model & Weights ──────────────────────────────────────────────────────────
DEFAULT_MODEL_NAME = "yolov8n"
DEFAULT_WEIGHTS = "yolov8n.pt"

# ── Detection & Confidence Thresholds ────────────────────────────────────────
# Minimum confidence required to emit a valid road damage event (per event-schema.md)
CONFIDENCE_THRESHOLD = 0.65
IOU_THRESHOLD = 0.45

# ── Severity Scoring Thresholds ──────────────────────────────────────────────
# Relative bounding box area (bbox_area / image_area) and width ratio thresholds
SEVERITY_THRESHOLDS = {
    "high_area_ratio": 0.06,      # >= 6% of frame area is High severity
    "high_width_ratio": 0.22,     # >= 22% of frame width is High severity
    "medium_area_ratio": 0.015,   # >= 1.5% of frame area is Medium severity
    "medium_width_ratio": 0.09,   # >= 9% of frame width is Medium severity
}

# ── Class Mappings ───────────────────────────────────────────────────────────
DEFAULT_ROAD_CLASSES = {
    0: "pothole",
    1: "road_defect",
    2: "crack",
}

# ── Paths ────────────────────────────────────────────────────────────────────
MODULE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_ROOT.parents[1]
DEFAULT_EVIDENCE_DIR = MODULE_ROOT / "evidence"

# Sample video locations for testing and demo runs
SAMPLE_VIDEOS = {
    "city": PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model" / "cityRoad_potHoles.mp4",
    "city_side": PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model" / "cityRoad_potHoles-side.mp4",
    "rural": PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model" / "ruralRoad_potHoles.mp4",
}
