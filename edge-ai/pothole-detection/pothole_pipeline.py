"""
pothole_pipeline.py
-------------------
End-to-end video and image inference pipeline for Pothole and Road Damage AI.
"""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Generator, List, Optional, Union
import cv2
import numpy as np

from pothole_config import (
    DEFAULT_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEFAULT_EVIDENCE_DIR,
)
from pothole_detector import PotholeDetector
from pothole_event_schema import PotholeDetection, PotholeFrameSummary


class PotholePipeline:
    def __init__(
        self,
        source: Union[str, int] = 0,
        model_path: str = DEFAULT_WEIGHTS,
        conf_thresh: float = CONFIDENCE_THRESHOLD,
        iou_thresh: float = IOU_THRESHOLD,
        show: bool = False,
        save_evidence: bool = True,
        evidence_dir: Optional[str] = None,
        emit_interval_seconds: float = 1.0,
    ) -> None:
        self.source = source
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.show = show
        self.save_evidence = save_evidence
        self.evidence_dir = Path(evidence_dir or DEFAULT_EVIDENCE_DIR)
        self.emit_interval_seconds = emit_interval_seconds

        if self.save_evidence:
            self.evidence_dir.mkdir(parents=True, exist_ok=True)

        self.detector = PotholeDetector(
            model_path=model_path,
            conf=conf_thresh,
            iou=iou_thresh,
        )

    def is_image_file(self, path: Union[str, int]) -> bool:
        if isinstance(path, int):
            return False
        ext = Path(str(path)).suffix.lower()
        return ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

    def run_on_image(self, image_path: str) -> List[dict]:
        frame = cv2.imread(image_path)
        if frame is None:
            raise FileNotFoundError(f"[PotholePipeline] Image not found: {image_path}")

        evidence_path = str(self.evidence_dir / f"evidence_{Path(image_path).stem}.jpg") if self.save_evidence else None
        detections = self.detector.detect(frame, source_frame=0, save_evidence_path=evidence_path)

        if self.show:
            cv2.imshow("Pothole AI - Single Image", frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return [d.to_dict() for d in detections]

    def run(self) -> Generator[dict, None, None]:
        if self.is_image_file(self.source):
            for event in self.run_on_image(str(self.source)):
                yield event
            return

        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"[PotholePipeline] Cannot open video source: {self.source}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frames_per_emit = max(1, int(fps * self.emit_interval_seconds))
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                save_path = None
                if self.save_evidence and (frame_idx % frames_per_emit == 0):
                    save_path = str(self.evidence_dir / f"evidence_frame_{frame_idx:06d}.jpg")

                detections = self.detector.detect(
                    frame=frame,
                    source_frame=frame_idx,
                    save_evidence_path=save_path,
                )

                if detections:
                    worst_severity = self.detector.worst_severity(detections)
                    best_detection = next((d for d in detections if d.severity == worst_severity), detections[0])

                    if frame_idx % frames_per_emit == 0:
                        yield best_detection.to_dict()

                if self.show:
                    for d in detections:
                        self.detector.draw_box(frame, d)
                    cv2.imshow("Pothole & Road Damage AI Pipeline", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                frame_idx += 1

        finally:
            cap.release()
            if self.show:
                cv2.destroyAllWindows()
