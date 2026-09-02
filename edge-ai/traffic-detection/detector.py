"""
detector.py
-----------
Wraps YOLOv8 inference and filters only vehicle-class detections.

Dependencies:
    pip install ultralytics>=8.0.0

YOLOv8 weights are auto-downloaded from Ultralytics on first run (~6 MB for yolov8n).
No manual download needed.

Usage:
    detector = VehicleDetector(model_name="yolov8n")
    detections = detector.detect(frame)
    # detections → list of Detection namedtuples
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError(
        "ultralytics package not found.\n"
        "Install it with:  pip install ultralytics>=8.0.0"
    )

from config import (
    MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    COCO_VEHICLE_CLASSES,
)


@dataclass
class Detection:
    """
    Single vehicle detection for one frame.

    Attributes:
        bbox        : (x1, y1, x2, y2) in pixel coordinates
        class_name  : one of "car", "bike", "bus", "truck"
        confidence  : float in [0, 1]
        coco_id     : original COCO class id (int)
    """
    bbox: Tuple[int, int, int, int]
    class_name: str
    confidence: float
    coco_id: int

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return max(0, x2 - x1) * max(0, y2 - y1)

    def to_xywh(self) -> Tuple[int, int, int, int]:
        x1, y1, x2, y2 = self.bbox
        return (x1, y1, x2 - x1, y2 - y1)

    def to_array(self) -> np.ndarray:
        """Returns [x1, y1, x2, y2, confidence] for SORT."""
        x1, y1, x2, y2 = self.bbox
        return np.array([x1, y1, x2, y2, self.confidence])


class VehicleDetector:
    """
    Runs YOLOv8 on a frame and returns only vehicle detections.

    Args:
        model_name  : YOLOv8 variant — "yolov8n" | "yolov8s" | "yolov8m" etc.
        conf        : detection confidence threshold
        iou         : NMS IoU threshold
        device      : "cpu" | "cuda" | "mps" — None lets ultralytics auto-select
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        conf: float = CONFIDENCE_THRESHOLD,
        iou: float = IOU_THRESHOLD,
        device: str | None = None,
    ) -> None:
        self.conf = conf
        self.iou  = iou
        print(f"[VehicleDetector] Loading {model_name} …")
        self.model = YOLO(f"{model_name}.pt")
        self.device = device
        print(f"[VehicleDetector] Model ready. Vehicle classes: {list(set(COCO_VEHICLE_CLASSES.values()))}")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on a single BGR frame (numpy array).

        Returns:
            List of Detection objects — one per detected vehicle.
        """
        results = self.model(
            frame,
            conf=self.conf,
            iou=self.iou,
            device=self.device,
            verbose=False,
            classes=list(COCO_VEHICLE_CLASSES.keys()),  # pre-filter at YOLO level
        )[0]

        detections: List[Detection] = []

        if results.boxes is None:
            return detections

        for box in results.boxes:
            coco_id = int(box.cls[0].item())
            if coco_id not in COCO_VEHICLE_CLASSES:
                continue  # safety check (already filtered above)

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf_score = float(box.conf[0].item())

            detections.append(Detection(
                bbox=(int(x1), int(y1), int(x2), int(y2)),
                class_name=COCO_VEHICLE_CLASSES[coco_id],
                confidence=conf_score,
                coco_id=coco_id,
            ))

        return detections

    def mean_confidence(self, detections: List[Detection]) -> float:
        """Average confidence across a list of detections."""
        if not detections:
            return 0.0
        return sum(d.confidence for d in detections) / len(detections)

    def frame_coverage(self, detections: List[Detection], frame_h: int, frame_w: int) -> float:
        """
        Fraction of frame area covered by bounding boxes.
        Clipped to [0, 1].
        """
        total_area = frame_h * frame_w
        if total_area == 0:
            return 0.0
        covered = sum(d.area for d in detections)
        return min(1.0, covered / total_area)
