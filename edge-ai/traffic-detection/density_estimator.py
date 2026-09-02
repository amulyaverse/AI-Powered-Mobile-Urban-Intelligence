"""
density_estimator.py
---------------------
Traffic density estimation.

Combines:
  1. Instantaneous vehicle count in frame  (60 % weight)
  2. Frame coverage ratio — bbox area / total frame area  (40 % weight)

Maps the blended score to a density label: LOW | MEDIUM | HIGH | CRITICAL

Usage:
    estimator = DensityEstimator()
    result = estimator.estimate(
        in_frame_count=14,
        frame_coverage_ratio=0.22,
    )
    result.label          # "HIGH"
    result.score          # 0.78  (normalised 0–1)
    result.in_frame_count # 14
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import cv2

from config import DENSITY_THRESHOLDS, COVERAGE_WEIGHT


# Maximum vehicle count used for normalisation (soft cap)
_COUNT_MAX = 30


@dataclass
class DensityResult:
    label: str              # LOW | MEDIUM | HIGH | CRITICAL
    score: float            # normalised score 0.0 – 1.0
    in_frame_count: int     # total vehicles visible in this frame
    coverage_ratio: float   # fraction of frame covered by bboxes
    count_score: float      # component from count
    coverage_score: float   # component from coverage


# Map label → 0-based index for colouring
_LABEL_COLORS = {
    "LOW":      (0,   200,  0),    # green
    "MEDIUM":   (0,   200, 255),   # yellow
    "HIGH":     (0,   100, 255),   # orange
    "CRITICAL": (0,    0,  220),   # red
}


class DensityEstimator:
    """
    Stateless density estimator.

    Call `estimate()` once per frame (or per emit interval) to get
    a DensityResult.

    Args:
        coverage_weight : weight given to frame-coverage component (0–1).
                          Remainder is given to raw count component.
    """

    def __init__(self, coverage_weight: float = COVERAGE_WEIGHT) -> None:
        self.coverage_weight = coverage_weight
        self.count_weight    = 1.0 - coverage_weight

    def estimate(
        self,
        in_frame_count:      int,
        frame_coverage_ratio: float = 0.0,
    ) -> DensityResult:
        """
        Compute density for the current frame.

        Args:
            in_frame_count       : number of vehicles detected in this frame
            frame_coverage_ratio : fraction of frame area covered by bboxes (0–1)

        Returns:
            DensityResult with label and normalised score.
        """
        # Normalise count to [0, 1]
        count_score    = min(1.0, in_frame_count / _COUNT_MAX)
        coverage_score = float(np.clip(frame_coverage_ratio, 0.0, 1.0))

        blended = (
            self.count_weight    * count_score +
            self.coverage_weight * coverage_score
        )

        label = self._score_to_label(in_frame_count)

        return DensityResult(
            label=label,
            score=round(blended, 4),
            in_frame_count=in_frame_count,
            coverage_ratio=round(coverage_score, 4),
            count_score=round(count_score, 4),
            coverage_score=round(coverage_score, 4),
        )

    @staticmethod
    def _score_to_label(count: int) -> str:
        """Map raw count to a density label using configured thresholds."""
        for label, (lo, hi) in DENSITY_THRESHOLDS.items():
            if lo <= count <= hi:
                return label
        return "CRITICAL"

    # ── Drawing ───────────────────────────────────────────────────────────────

    @staticmethod
    def draw_hud(
        frame: np.ndarray,
        counts: dict,
        result: DensityResult,
        fps: float = 0.0,
    ) -> np.ndarray:
        """
        Overlay HUD panel on the top-left corner of the frame.
        Shows per-class counts, total, density label, and FPS.

        Args:
            frame   : BGR numpy array (modified in-place)
            counts  : vehicle counts dict from VehicleCounter
            result  : DensityResult from DensityEstimator
            fps     : frames per second (0 to hide)
        Returns:
            The annotated frame.
        """
        h, w = frame.shape[:2]
        panel_w = 280
        panel_h = 160
        alpha   = 0.55

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Counts
        labels_order = [("car", "Cars"), ("bike", "Bikes"), ("bus", "Buses"), ("truck", "Trucks")]
        y = 22
        x = 10
        for cls, display in labels_order:
            n = counts.get(cls, 0)
            cv2.putText(
                frame, f"{display}: {n:>3}",
                (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
                (220, 220, 220), 1, cv2.LINE_AA,
            )
            y += 22

        # Total
        cv2.putText(
            frame, f"Total:  {result.in_frame_count:>3}",
            (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
            (200, 200, 200), 1, cv2.LINE_AA,
        )
        y += 24

        # Density label (coloured)
        density_color = _LABEL_COLORS.get(result.label, (200, 200, 200))
        cv2.putText(
            frame, f"Density: {result.label}  ({result.score:.2f})",
            (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
            density_color, 2, cv2.LINE_AA,
        )
        y += 24

        # FPS
        if fps > 0:
            cv2.putText(
                frame, f"FPS: {fps:.1f}",
                (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                (150, 150, 150), 1, cv2.LINE_AA,
            )

        return frame
