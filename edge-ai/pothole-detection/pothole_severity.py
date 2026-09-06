"""
pothole_severity.py
-------------------
Deterministic and explainable severity scoring for road defects and potholes.
"""

from typing import Tuple, Dict, Any
from pothole_config import SEVERITY_THRESHOLDS


def calculate_severity(
    bbox: Tuple[int, int, int, int],
    frame_shape: Tuple[int, ...],
    confidence: float = 1.0,
) -> Tuple[str, Dict[str, Any]]:
    x1, y1, x2, y2 = bbox
    frame_h, frame_w = frame_shape[0], frame_shape[1]

    if frame_h <= 0 or frame_w <= 0:
        return "low", {"area_ratio": 0.0, "width_ratio": 0.0, "bbox_area": 0}

    bbox_w = max(0, x2 - x1)
    bbox_h = max(0, y2 - y1)
    bbox_area = bbox_w * bbox_h
    image_area = frame_h * frame_w

    area_ratio = bbox_area / image_area if image_area > 0 else 0.0
    width_ratio = bbox_w / frame_w if frame_w > 0 else 0.0

    high_area = SEVERITY_THRESHOLDS.get("high_area_ratio", 0.06)
    high_width = SEVERITY_THRESHOLDS.get("high_width_ratio", 0.22)
    med_area = SEVERITY_THRESHOLDS.get("medium_area_ratio", 0.015)
    med_width = SEVERITY_THRESHOLDS.get("medium_width_ratio", 0.09)

    if area_ratio >= high_area or width_ratio >= high_width:
        severity = "high"
    elif area_ratio >= med_area or width_ratio >= med_width:
        severity = "medium"
    else:
        severity = "low"

    metrics = {
        "bbox_area": int(bbox_area),
        "area_ratio": round(area_ratio, 4),
        "width_ratio": round(width_ratio, 4),
        "confidence": round(confidence, 4),
    }

    return severity, metrics
