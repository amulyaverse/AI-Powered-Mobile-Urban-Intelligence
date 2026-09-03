"""
tracker.py
----------
SORT (Simple Online and Realtime Tracking) implementation.

SORT uses Kalman Filters + Hungarian Algorithm for association.
It is lightweight (CPU-only, no extra model), making it ideal for edge devices.

Reference: Bewley et al., "Simple Online and Realtime Tracking" (2016)
           https://arxiv.org/abs/1602.00763

Dependencies:
    pip install numpy scipy filterpy

Usage:
    tracker = VehicleTracker()
    tracked = tracker.update(detections)
    for t in tracked:
        track_id = t.track_id
        bbox     = t.bbox
        class_name = t.class_name
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import linear_sum_assignment

try:
    from filterpy.kalman import KalmanFilter
except ImportError:
    raise ImportError(
        "filterpy not found.\n"
        "Install it with:  pip install filterpy"
    )

from detector import Detection
from config import SORT_MAX_AGE, SORT_MIN_HITS, SORT_IOU_THRESH


# ─── Kalman-tracked bounding box ─────────────────────────────────────────────

class KalmanBoxTracker:
    """
    Represents one tracked object using a Kalman Filter.
    State vector: [cx, cy, s, r, cx', cy', s']
        cx, cy  → centroid
        s       → scale (area)
        r       → aspect ratio (width/height, constant)
        primes  → velocities
    """
    _count = 0

    def __init__(self, detection: Detection) -> None:
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        # State transition
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
        ], dtype=float)
        # Measurement function
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
        ], dtype=float)
        self.kf.R[2:, 2:] *= 10.0
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P           *= 10.0
        self.kf.Q[-1, -1]  *= 0.01
        self.kf.Q[4:, 4:]  *= 0.01
        self.kf.x[:4]       = self._bbox_to_z(detection.bbox)

        KalmanBoxTracker._count += 1
        self.track_id: int = KalmanBoxTracker._count
        self.hits: int     = 1
        self.hit_streak: int = 1
        self.age: int      = 0
        self.time_since_update: int = 0
        self.class_name: str = detection.class_name
        self.confidence: float = detection.confidence
        self._history: List[np.ndarray] = []

    # ── Kalman helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _bbox_to_z(bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Convert [x1,y1,x2,y2] to [cx,cy,s,r]."""
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        cx = x1 + w / 2.0
        cy = y1 + h / 2.0
        s  = w * h
        r  = w / float(h) if h > 0 else 1.0
        return np.array([[cx], [cy], [s], [r]])

    @staticmethod
    def _z_to_bbox(z: np.ndarray) -> Tuple[int, int, int, int]:
        """Convert [cx,cy,s,r] back to [x1,y1,x2,y2]."""
        cx, cy, s, r = z[0, 0], z[1, 0], z[2, 0], z[3, 0]
        w = np.sqrt(abs(s * r))
        h = abs(s) / w if w > 0 else 0
        return (
            int(cx - w / 2), int(cy - h / 2),
            int(cx + w / 2), int(cy + h / 2),
        )

    def predict(self) -> Tuple[int, int, int, int]:
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] = 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        return self._z_to_bbox(self.kf.x)

    def update(self, detection: Detection) -> None:
        self.time_since_update = 0
        self._history = []
        self.hits += 1
        self.hit_streak += 1
        self.class_name = detection.class_name    # update class if changed
        self.confidence = detection.confidence
        self.kf.update(self._bbox_to_z(detection.bbox))

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        return self._z_to_bbox(self.kf.x)

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)


# ─── IoU helpers ─────────────────────────────────────────────────────────────

def _iou(bb1: Tuple, bb2: Tuple) -> float:
    ax1, ay1, ax2, ay2 = bb1
    bx1, by1, bx2, by2 = bb2
    ix1 = max(ax1, bx1);  iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2);  iy2 = min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    a1 = (ax2 - ax1) * (ay2 - ay1)
    a2 = (bx2 - bx1) * (by2 - by1)
    return inter / (a1 + a2 - inter + 1e-6)


def _iou_matrix(trackers: List[KalmanBoxTracker], dets: List[Detection]) -> np.ndarray:
    mat = np.zeros((len(trackers), len(dets)))
    for i, trk in enumerate(trackers):
        for j, det in enumerate(dets):
            mat[i, j] = _iou(trk.bbox, det.bbox)
    return mat


# ─── Public tracker ──────────────────────────────────────────────────────────

@dataclass
class TrackedVehicle:
    """One tracked vehicle returned per frame."""
    track_id: int
    bbox: Tuple[int, int, int, int]
    class_name: str
    confidence: float

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)


class VehicleTracker:
    """
    SORT tracker — maintains active tracks across frames.

    Args:
        max_age    : frames to keep a lost track alive
        min_hits   : minimum detections before track is confirmed
        iou_thresh : IoU threshold for detection–track association
    """

    def __init__(
        self,
        max_age:    int   = SORT_MAX_AGE,
        min_hits:   int   = SORT_MIN_HITS,
        iou_thresh: float = SORT_IOU_THRESH,
    ) -> None:
        self.max_age    = max_age
        self.min_hits   = min_hits
        self.iou_thresh = iou_thresh
        self._trackers: List[KalmanBoxTracker] = []
        self._frame_count: int = 0
        KalmanBoxTracker._count = 0  # reset IDs on new tracker instance

    def update(self, detections: List[Detection]) -> List[TrackedVehicle]:
        """
        Feed detections for the current frame; get back confirmed tracks.

        Args:
            detections : output from VehicleDetector.detect()
        Returns:
            List of TrackedVehicle — only confirmed tracks (hit_streak >= min_hits)
        """
        self._frame_count += 1

        # 1. Predict new positions for all existing tracks
        predicted_bboxes = [trk.predict() for trk in self._trackers]

        # 2. Associate detections with tracks via Hungarian Algorithm on IoU
        matched, unmatched_dets, unmatched_trks = self._associate(detections)

        # 3. Update matched tracks
        for trk_idx, det_idx in matched:
            self._trackers[trk_idx].update(detections[det_idx])

        # 4. Create new tracks for unmatched detections
        for det_idx in unmatched_dets:
            self._trackers.append(KalmanBoxTracker(detections[det_idx]))

        # 5. Remove dead tracks
        self._trackers = [
            trk for trk in self._trackers
            if trk.time_since_update <= self.max_age
        ]

        # 6. Return only confirmed tracks
        confirmed: List[TrackedVehicle] = []
        for trk in self._trackers:
            if trk.hit_streak >= self.min_hits or self._frame_count <= self.min_hits:
                confirmed.append(TrackedVehicle(
                    track_id=trk.track_id,
                    bbox=trk.bbox,
                    class_name=trk.class_name,
                    confidence=trk.confidence,
                ))
        return confirmed

    def _associate(
        self,
        detections: List[Detection],
    ) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """Hungarian-algorithm matching. Returns (matched, unmatched_dets, unmatched_trks)."""
        if not self._trackers or not detections:
            return [], list(range(len(detections))), list(range(len(self._trackers)))

        iou_mat = _iou_matrix(self._trackers, detections)
        trk_idxs, det_idxs = linear_sum_assignment(-iou_mat)

        matched = [
            (t, d) for t, d in zip(trk_idxs, det_idxs)
            if iou_mat[t, d] >= self.iou_thresh
        ]
        matched_trk = {m[0] for m in matched}
        matched_det = {m[1] for m in matched}

        unmatched_dets = [i for i in range(len(detections)) if i not in matched_det]
        unmatched_trks = [i for i in range(len(self._trackers)) if i not in matched_trk]
        return matched, unmatched_dets, unmatched_trks

    @property
    def active_count(self) -> int:
        return len(self._trackers)
