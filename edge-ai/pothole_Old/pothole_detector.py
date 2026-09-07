"""
pothole_detector.py
-------------------
Pothole & Road Defect Detector wrapping YOLOv8 inference.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import cv2
import torch

_original_load = torch.load
def _safe_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_load(*args, **kwargs)
torch.load = _safe_load

from ultralytics import YOLO

from pothole_config import (
    DEFAULT_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEFAULT_ROAD_CLASSES,
)
from pothole_severity import calculate_severity
from pothole_event_schema import PotholeDetection


class PotholeDetector:
    def __init__(
        self,
        model_path: str = DEFAULT_WEIGHTS,
        conf: float = CONFIDENCE_THRESHOLD,
        iou: float = IOU_THRESHOLD,
        device: str | None = None,
    ) -> None:
        self.conf = conf
        self.iou = iou
        self.device = device
        self.model_path = model_path
        self.model = YOLO(model_path)

    def get_class_name(self, class_id: int) -> str:
        if hasattr(self.model, "names") and self.model.names and class_id in self.model.names:
            name = str(self.model.names[class_id]).lower()
            return name if name in ["pothole", "road_defect", "crack"] else "pothole"
        return DEFAULT_ROAD_CLASSES.get(class_id, "pothole")

    def detect(
        self,
        frame: np.ndarray,
        source_frame: int = 0,
        save_evidence_path: Optional[str] = None,
    ) -> List[PotholeDetection]:
        if frame is None or frame.size == 0:
            return []

        frame_h, frame_w = frame.shape[:2]
        results = self.model(
            frame,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
        )[0]

        detections: List[PotholeDetection] = []

        if results.boxes is None or len(results.boxes) == 0:
            return detections

        annotated_frame = frame.copy() if save_evidence_path else None

        for box in results.boxes:
            conf_score = float(box.conf[0].item())
            if conf_score < self.conf:
                continue

            class_id = int(box.cls[0].item())
            class_name = self.get_class_name(class_id)
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            bbox_tuple = (int(x1), int(y1), int(x2), int(y2))

            severity, metrics = calculate_severity(
                bbox=bbox_tuple,
                frame_shape=(frame_h, frame_w),
                confidence=conf_score,
            )

            detection = PotholeDetection(
                bbox=bbox_tuple,
                class_name=class_name,
                confidence=conf_score,
                severity=severity,
                area_ratio=metrics["area_ratio"],
                source_frame=source_frame,
                evidence=str(save_evidence_path) if save_evidence_path else "",
            )
            detections.append(detection)

            if annotated_frame is not None:
                self.draw_box(annotated_frame, detection)

        if save_evidence_path and detections and annotated_frame is not None:
            os.makedirs(os.path.dirname(os.path.abspath(save_evidence_path)), exist_ok=True)
            cv2.imwrite(save_evidence_path, annotated_frame)

        return detections

    @staticmethod
    def draw_box(img: np.ndarray, detection: PotholeDetection) -> None:
        x1, y1, x2, y2 = detection.bbox
        color = (0, 0, 255) if detection.severity == "high" else (
            (0, 165, 255) if detection.severity == "medium" else (0, 255, 0)
        )
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        tag = f"{detection.class_name.upper()} {detection.severity.upper()} ({detection.confidence:.0%})"
        cv2.putText(img, tag, (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def mean_confidence(self, detections: List[PotholeDetection]) -> float:
        if not detections:
            return 0.0
        return sum(d.confidence for d in detections) / len(detections)

    def worst_severity(self, detections: List[PotholeDetection]) -> Optional[str]:
        if not detections:
            return None
        severities = {d.severity for d in detections}
        if "high" in severities:
            return "high"
        if "medium" in severities:
            return "medium"
        return "low"
