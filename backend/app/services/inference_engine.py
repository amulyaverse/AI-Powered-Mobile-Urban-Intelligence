"""
services/inference_engine.py
-----------------------------
Wraps YOLO models (traffic detection and pothole detection) behind
a single unified interface for use by the WebSocket camera endpoint.

Usage:
    engine = InferenceEngine(mode="traffic")
    result = engine.run(frame_bgr_ndarray, frame_index=42)
    if result:
        payload = result.to_ws_payload(event_id="EVT_abc123")
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Optional, List

from ultralytics import YOLO
import numpy as np

from app.config import get_settings

settings = get_settings()

# COCO class names used by the default YOLOv8 weights.
# We map these to our internal vehicle categories.
TRAFFIC_CLASS_MAP: dict[str, str] = {
    "car":        "car",
    "motorcycle": "bike",
    "bus":        "bus",
    "truck":      "truck",
    "bicycle":    "bike",
}

# Classes that indicate a pothole / road defect
POTHOLE_CLASSES = {"pothole", "road_defect", "crack", "defect"}

# Map total vehicle count to traffic density label and score
def _density_from_count(total: int) -> tuple[str, float]:
    if total >= 30:
        return "CRITICAL", 1.0
    if total >= 20:
        return "HIGH", 0.75
    if total >= 10:
        return "MEDIUM", 0.50
    return "LOW", 0.25

def _density_to_severity(density: str) -> str:
    return {"LOW": "low", "MEDIUM": "medium", "HIGH": "high", "CRITICAL": "critical"}.get(density, "low")


def _fuse_pothole_boxes(
    boxes: "List[BoundingBox]", distance_threshold: int = 60
) -> "List[BoundingBox]":
    """
    Spatial cluster-fusion — ports ``cluster_boxes()`` from
    ``edge-ai/pothole-latest/Pothole_Road_Condition_Model/pothole_severity.py``
    into the backend inference path so Live Monitoring matches the standalone
    pothole pipeline output.

    Iteratively merges any two BoundingBox objects whose edges are within
    *distance_threshold* pixels of each other into a single hull box, taking
    the maximum confidence and preserving the class_name of the first box.
    """
    if not boxes:
        return []

    # Work on mutable dicts, convert back at the end
    clusters = [
        {
            "x1": b.x1, "y1": b.y1, "x2": b.x2, "y2": b.y2,
            "conf": b.confidence, "class_name": b.class_name,
            "track_id": b.track_id,
        }
        for b in boxes
    ]

    changed = True
    while changed:
        changed = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                c1, c2 = clusters[i], clusters[j]
                # Merge if boxes overlap or are within distance_threshold px
                if not (
                    c1["x2"] < c2["x1"] - distance_threshold
                    or c1["x1"] > c2["x2"] + distance_threshold
                    or c1["y2"] < c2["y1"] - distance_threshold
                    or c1["y1"] > c2["y2"] + distance_threshold
                ):
                    c1["x1"] = min(c1["x1"], c2["x1"])
                    c1["y1"] = min(c1["y1"], c2["y1"])
                    c1["x2"] = max(c1["x2"], c2["x2"])
                    c1["y2"] = max(c1["y2"], c2["y2"])
                    c1["conf"] = max(c1["conf"], c2["conf"])
                    clusters.pop(j)
                    changed = True
                    break
            if changed:
                break

    return [
        BoundingBox(
            x1=c["x1"], y1=c["y1"], x2=c["x2"], y2=c["y2"],
            class_name=c["class_name"],
            confidence=c["conf"],
            track_id=c.get("track_id"),
        )
        for c in clusters
    ]


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    class_name: str
    confidence: float
    track_id: Optional[int] = None

    def area_ratio(self, frame_w: int, frame_h: int) -> float:
        """Fraction of the total frame area covered by this box."""
        box_area = (self.x2 - self.x1) * (self.y2 - self.y1)
        total_area = frame_w * frame_h
        return box_area / total_area if total_area > 0 else 0.0


@dataclass
class InferenceResult:
    """Structured output from a single YOLO inference pass."""
    event_type: str                       # "vehicle_count" | "pothole" | "road_defect"
    confidence: float                     # highest detection confidence in the frame
    severity: str                         # low | medium | high | critical
    boxes: List[BoundingBox]
    frame_index: int
    frame_coverage_ratio: float           # sum of box areas / frame area

    # Traffic-specific (None for pothole mode)
    car_count: Optional[int] = None
    bike_count: Optional[int] = None
    bus_count: Optional[int] = None
    truck_count: Optional[int] = None
    total_vehicles: Optional[int] = None
    density: Optional[str] = None
    density_score: Optional[float] = None

    # Pothole / road defect specific (PR 37 & 40)
    width_ratio: Optional[float] = None
    area_ratio: Optional[float] = None
    severity_method: Optional[str] = None
    surface_condition: Optional[str] = None

    def to_ws_payload(self, event_id: str, evidence: Optional[str] = None) -> dict:
        """Compact JSON payload sent back to the edge publisher and broadcasted to dashboard clients."""
        return {
            "event_id": event_id,
            "evidence": evidence,
            "event_type": self.event_type,
            "confidence": round(self.confidence, 4),
            "severity": self.severity,
            "frame_index": self.frame_index,
            "frame_coverage_ratio": round(self.frame_coverage_ratio, 4),
            "width_ratio": self.width_ratio,
            "area_ratio": self.area_ratio,
            "severity_method": self.severity_method,
            "surface_condition": self.surface_condition,
            "boxes": [
                {
                    "x1": round(b.x1, 1),
                    "y1": round(b.y1, 1),
                    "x2": round(b.x2, 1),
                    "y2": round(b.y2, 1),
                    "class": b.class_name,
                    "conf": round(b.confidence, 3),
                    "track_id": b.track_id,
                }
                for b in self.boxes
            ],
            # Traffic fields (included for vehicle_count events only)
            **(
                {
                    "car_count": self.car_count,
                    "bike_count": self.bike_count,
                    "bus_count": self.bus_count,
                    "truck_count": self.truck_count,
                    "total_vehicles": self.total_vehicles,
                    "density": self.density,
                    "density_score": self.density_score,
                }
                if self.event_type == "vehicle_count"
                else {}
            ),
        }


class InferenceEngine:
    """
    Lazy-loading YOLO inference engine.

    The model is not loaded at construction time; it is loaded on the first
    call to run() so that startup latency is minimised and unused engines
    (e.g. pothole mode when no pothole camera is connected) cost nothing.
    """

    def __init__(self, mode: Literal["traffic", "pothole"] = "traffic"):
        self._mode = mode
        self._model = None   # loaded on demand

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            import os
            from pathlib import Path
            import torch
            
            # Allowlist Ultralytics model classes for PyTorch 2.6+ unpickling
            try:
                import ultralytics.nn.tasks
                if hasattr(torch.serialization, "add_safe_globals"):
                    torch.serialization.add_safe_globals([
                        ultralytics.nn.tasks.DetectionModel,
                        ultralytics.nn.tasks.SegmentationModel,
                        ultralytics.nn.tasks.ClassificationModel,
                        ultralytics.nn.tasks.PoseModel,
                        ultralytics.nn.tasks.OBBModel,
                        ultralytics.nn.tasks.WorldModel,
                    ])
            except Exception:
                pass

            # Safe monkeypatch for PyTorch 2.6+ weights_only default
            _orig_load = torch.load
            def _compat_torch_load(*args, **kwargs):
                if "weights_only" not in kwargs:
                    kwargs["weights_only"] = False
                return _orig_load(*args, **kwargs)
            torch.load = _compat_torch_load

            from ultralytics import YOLO
            weights = (
                settings.YOLO_TRAFFIC_WEIGHTS
                if self._mode == "traffic"
                else settings.YOLO_POTHOLE_WEIGHTS
            )
            # Resolve relative paths against PROJECT_ROOT and convert to CWD-relative path
            if not os.path.exists(weights):
                from app.config import PROJECT_ROOT
                candidate = PROJECT_ROOT / weights
                if candidate.exists():
                    weights = os.path.relpath(str(candidate), start=os.getcwd())

            self._model = YOLO(weights)
        except Exception as exc:
            raise RuntimeError(
                f"[InferenceEngine] Failed to load YOLO model ({self._mode}): {exc}"
            ) from exc

    def _parse_traffic(
        self, results, frame_index: int, frame_h: int, frame_w: int
    ) -> Optional[InferenceResult]:
        """Parse COCO vehicle classes from a traffic detection result."""
        boxes: List[BoundingBox] = []
        counts: dict[str, int] = {"car": 0, "bike": 0, "bus": 0, "truck": 0}
        max_conf = 0.0

        res = results[0]
        if res.boxes is None or len(res.boxes) == 0:
            return None

        track_ids = (
            res.boxes.id.int().cpu().tolist()
            if res.boxes.id is not None
            else [None] * len(res.boxes)
        )
        names = res.names

        for i, box in enumerate(res.boxes):
            cls_idx = int(box.cls.cpu().item())
            cls_name = names[cls_idx].lower()
            conf = float(box.conf.cpu().item())
            mapped = TRAFFIC_CLASS_MAP.get(cls_name)
            if mapped is None:
                continue  # ignore non-vehicle classes (person, etc.)

            xyxy = box.xyxy.cpu().tolist()[0]
            bb = BoundingBox(
                x1=xyxy[0], y1=xyxy[1], x2=xyxy[2], y2=xyxy[3],
                class_name=mapped,
                confidence=conf,
                track_id=track_ids[i],
            )
            boxes.append(bb)
            counts[mapped] = counts.get(mapped, 0) + 1
            max_conf = max(max_conf, conf)

        if not boxes:
            return None

        total = sum(counts.values())
        density, density_score = _density_from_count(total)
        coverage = sum(b.area_ratio(frame_w, frame_h) for b in boxes)

        return InferenceResult(
            event_type="vehicle_count",
            confidence=round(max_conf, 4),
            severity=_density_to_severity(density),
            boxes=boxes,
            frame_index=frame_index,
            frame_coverage_ratio=round(min(coverage, 1.0), 4),
            car_count=counts["car"],
            bike_count=counts["bike"],
            bus_count=counts["bus"],
            truck_count=counts["truck"],
            total_vehicles=total,
            density=density,
            density_score=density_score,
        )

    def _parse_pothole(
        self, results, frame_index: int, frame_h: int, frame_w: int
    ) -> Optional[InferenceResult]:
        """Parse pothole / road_defect detections from a pothole model result.

        Two post-processing steps match the standalone pothole-latest pipeline:
        1. Per-box confidence gate (INFERENCE_CONFIDENCE_POTHOLE) to suppress
           low-quality predictions that were being displayed in Live Monitoring.
        2. Spatial cluster fusion (_fuse_pothole_boxes) to merge fragmented /
           overlapping boxes into a single unified defect boundary per cluster,
           equivalent to ``cluster_boxes(distance_threshold=60)`` in
           ``pothole_severity.py``.
        """
        raw_boxes: List[BoundingBox] = []

        res = results[0]
        if res.boxes is None or len(res.boxes) == 0:
            return None

        track_ids = (
            res.boxes.id.int().cpu().tolist()
            if res.boxes.id is not None
            else [None] * len(res.boxes)
        )
        names = res.names

        # Pothole-specific Live Monitoring confidence gate
        conf_threshold = settings.INFERENCE_CONFIDENCE_POTHOLE

        for i, box in enumerate(res.boxes):
            cls_idx = int(box.cls.cpu().item())
            cls_name = names[cls_idx].lower()
            conf = float(box.conf.cpu().item())

            # Discard detections below the pothole-specific threshold
            if conf < conf_threshold:
                continue

            # Accept the class if it sounds like a road defect
            event_cls = "pothole"
            if "defect" in cls_name or "crack" in cls_name:
                event_cls = "road_defect"

            xyxy = box.xyxy.cpu().tolist()[0]
            raw_boxes.append(BoundingBox(
                x1=xyxy[0], y1=xyxy[1], x2=xyxy[2], y2=xyxy[3],
                class_name=event_cls,
                confidence=conf,
                track_id=track_ids[i],
            ))

        if not raw_boxes:
            return None

        # Spatial cluster fusion — fuse fragmented / overlapping boxes (matches
        # ``cluster_boxes(distance_threshold=60)`` in the standalone pipeline)
        boxes = _fuse_pothole_boxes(raw_boxes, distance_threshold=60)

        max_conf = max(b.confidence for b in boxes)
        coverage = sum(b.area_ratio(frame_w, frame_h) for b in boxes)
        dominant = max(set(b.class_name for b in boxes), key=lambda c: sum(1 for b in boxes if b.class_name == c))

        # PR 37 Approach A width heuristic + area ratio formulation
        max_box_w = max((b.x2 - b.x1) for b in boxes)
        max_width_ratio = max_box_w / frame_w if frame_w > 0 else 0.0
        max_area_ratio = max(b.area_ratio(frame_w, frame_h) for b in boxes)

        if max_width_ratio >= 0.22 or max_area_ratio >= 0.06:
            severity = "high"
        elif max_width_ratio >= 0.09 or max_area_ratio >= 0.015:
            severity = "medium"
        else:
            severity = "low"

        return InferenceResult(
            event_type=dominant,
            confidence=round(max_conf, 4),
            severity=severity,
            boxes=boxes,
            frame_index=frame_index,
            frame_coverage_ratio=round(min(coverage, 1.0), 4),
            width_ratio=round(max_width_ratio, 4),
            area_ratio=round(max_area_ratio, 4),
            severity_method="width_heuristic_pr37",
            surface_condition=dominant,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def run(self, frame: np.ndarray, frame_index: int = 0) -> Optional[InferenceResult]:
        """
        Run YOLO inference on a single BGR frame (numpy ndarray from OpenCV).

        Returns an InferenceResult if any relevant detections pass the
        confidence threshold, otherwise returns None.
        """
        if self._model is None:
            self._load()

        h, w = frame.shape[:2]

        try:
            if self._mode == "pothole":
                results = self._model.predict(
                    frame,
                    conf=settings.INFERENCE_CONFIDENCE,
                    iou=settings.INFERENCE_IOU,
                    verbose=False,
                )
            else:
                try:
                    results = self._model.track(
                        frame,
                        persist=True,
                        conf=settings.INFERENCE_CONFIDENCE,
                        iou=settings.INFERENCE_IOU,
                        verbose=False,
                    )
                except Exception:
                    # Fallback to direct detection if tracker dependency is unavailable
                    results = self._model.predict(
                        frame,
                        conf=settings.INFERENCE_CONFIDENCE,
                        iou=settings.INFERENCE_IOU,
                        verbose=False,
                    )
        except Exception as exc:
            print(f"[InferenceEngine] YOLO inference error: {exc}")
            return None

        if self._mode == "traffic":
            return self._parse_traffic(results, frame_index, h, w)
        else:
            return self._parse_pothole(results, frame_index, h, w)
