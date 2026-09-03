"""
pipeline.py
-----------
Main orchestrator: ties Detector → Tracker → Counter → DensityEstimator together.

This is the class that runs on the bus edge device (or a laptop for testing).
It processes a video file or webcam stream frame-by-frame and:
  - Annotates each frame with bounding boxes, track IDs, and HUD
  - Emits a TrafficEvent JSON every EVENT_EMIT_INTERVAL_SEC

Usage:
    pipeline = TrafficPipeline(source="video.mp4")
    for event in pipeline.run():
        print(event.summary())
        # send event to backend here
"""

from __future__ import annotations
from typing import Generator, Optional
import time
import cv2
import numpy as np

from config import (
    MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    EVENT_EMIT_INTERVAL_SEC,
    SHOW_FPS,
    SHOW_HUD,
)
from detector import VehicleDetector
from tracker import VehicleTracker
from counter import VehicleCounter
from density_estimator import DensityEstimator, DensityResult
from event_schema import TrafficEvent, GPSCoordinate


class TrafficPipeline:
    """
    Full Vehicle AI pipeline.

    Args:
        source      : path to video file, or integer camera index (e.g. 0)
        model_name  : YOLOv8 variant to use
        conf        : detection confidence threshold
        iou         : NMS IoU threshold
        show        : display annotated frames in a window
        save_path   : path to save annotated video (None = don't save)
        bus_id      : identifier for this bus/device
        gps_fn      : optional callable() → (lat, lon) for real GPS integration
        emit_interval : emit a TrafficEvent every N seconds of video
    """

    def __init__(
        self,
        source: str | int = 0,
        model_name:    str   = MODEL_NAME,
        conf:          float = CONFIDENCE_THRESHOLD,
        iou:           float = IOU_THRESHOLD,
        show:          bool  = False,
        save_path:     Optional[str] = None,
        bus_id:        str   = "BUS-UNKNOWN",
        gps_fn=None,
        emit_interval: float = EVENT_EMIT_INTERVAL_SEC,
    ) -> None:
        self.source        = source
        self.show          = show
        self.save_path     = save_path
        self.bus_id        = bus_id
        self.gps_fn        = gps_fn
        self.emit_interval = emit_interval

        self._detector  = VehicleDetector(model_name=model_name, conf=conf, iou=iou)
        self._tracker   = VehicleTracker()
        self._density   = DensityEstimator()

        # Counter is initialised once frame size is known
        self._counter: Optional[VehicleCounter] = None

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> Generator[TrafficEvent, None, None]:
        """
        Process the video source frame-by-frame.

        Yields a TrafficEvent once every `emit_interval` seconds.
        Annotated frames are optionally displayed / saved.

        Usage:
            for event in pipeline.run():
                send_to_backend(event)
        """
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"[Pipeline] Cannot open source: {self.source!r}")

        fps_video   = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames= int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(
            f"[Pipeline] Source: {self.source}  |  "
            f"{frame_w}×{frame_h} @ {fps_video:.1f} fps  |  "
            f"{total_frames if total_frames > 0 else '?'} frames"
        )

        self._counter = VehicleCounter(frame_h, frame_w)

        writer: Optional[cv2.VideoWriter] = None
        if self.save_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(self.save_path, fourcc, fps_video, (frame_w, frame_h))

        frames_per_emit = max(1, int(fps_video * self.emit_interval))
        frame_idx       = 0
        t_wall_start    = time.time()

        # Accumulators for the current emit window
        _confs:      list[float] = []
        _coverages:  list[float] = []
        _in_frame_counts: list[int] = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                t_frame_start = time.time()

                # ── Detect ────────────────────────────────────────────────
                detections = self._detector.detect(frame)

                # ── Track ─────────────────────────────────────────────────
                tracked = self._tracker.update(detections)

                # ── Count ─────────────────────────────────────────────────
                counts = self._counter.update(tracked)

                # ── Density ───────────────────────────────────────────────
                coverage = self._detector.frame_coverage(detections, frame_h, frame_w)
                density  = self._density.estimate(len(tracked), coverage)

                # Accumulate for event window
                if detections:
                    _confs.extend(d.confidence for d in detections)
                _coverages.append(coverage)
                _in_frame_counts.append(len(tracked))

                # ── Annotate frame ────────────────────────────────────────
                self._counter.draw_line(frame)
                self._counter.draw_tracks(frame, tracked)

                if SHOW_HUD:
                    elapsed  = time.time() - t_frame_start
                    fps_live = 1.0 / elapsed if elapsed > 0 else 0.0
                    DensityEstimator.draw_hud(frame, counts, density, fps=fps_live if SHOW_FPS else 0)

                if self.show:
                    cv2.imshow("Vehicle AI — SIH 2026", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("[Pipeline] User quit.")
                        break

                if writer:
                    writer.write(frame)

                # ── Emit event ────────────────────────────────────────────
                if frame_idx > 0 and frame_idx % frames_per_emit == 0:
                    event = self._build_event(
                        counts=counts,
                        in_frame_counts=_in_frame_counts,
                        coverages=_coverages,
                        confs=_confs,
                        frame_idx=frame_idx,
                    )
                    print(event.summary())
                    _confs.clear(); _coverages.clear(); _in_frame_counts.clear()
                    yield event

                frame_idx += 1

        finally:
            cap.release()
            if writer:
                writer.release()
            if self.show:
                cv2.destroyAllWindows()

        elapsed_total = time.time() - t_wall_start
        print(
            f"[Pipeline] Done. {frame_idx} frames in {elapsed_total:.1f}s "
            f"({frame_idx / elapsed_total:.1f} fps avg)"
        )

    # ── Event builder ─────────────────────────────────────────────────────────

    def _build_event(
        self,
        counts:          dict,
        in_frame_counts: list,
        coverages:       list,
        confs:           list,
        frame_idx:       int,
    ) -> TrafficEvent:
        """Construct a TrafficEvent from the accumulated window data."""
        avg_count    = float(np.mean(in_frame_counts)) if in_frame_counts else 0.0
        avg_coverage = float(np.mean(coverages)) if coverages else 0.0
        avg_conf     = float(np.mean(confs)) if confs else 0.0
        density_res  = self._density.estimate(round(avg_count), avg_coverage)

        # GPS
        gps = GPSCoordinate()
        if self.gps_fn:
            try:
                lat, lon = self.gps_fn()
                gps = GPSCoordinate(lat=lat, lon=lon)
            except Exception:
                pass

        return TrafficEvent(
            bus_id=self.bus_id,
            gps=gps,
            vehicle_counts={
                "car":   counts.get("car",   0),
                "bike":  counts.get("bike",  0),
                "bus":   counts.get("bus",   0),
                "truck": counts.get("truck", 0),
            },
            total_vehicles=sum(counts.values()),
            density=density_res.label,
            density_score=density_res.score,
            frame_coverage_ratio=round(avg_coverage, 4),
            confidence=round(avg_conf, 4),
            source_frame=frame_idx,
        )
