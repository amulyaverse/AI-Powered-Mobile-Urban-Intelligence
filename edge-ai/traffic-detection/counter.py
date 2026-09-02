"""
counter.py
----------
Line-crossing vehicle counter.

Draws a virtual horizontal counting line across the frame.
When a tracked vehicle's centroid crosses the line (in either direction),
its class-specific count is incremented exactly once (per track ID).

Usage:
    counter = VehicleCounter(frame_height=720)
    counts  = counter.update(tracked_vehicles)
    counts.get("car")  # → 7
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import numpy as np
import cv2

from tracker import TrackedVehicle
from config import (
    COUNTING_LINE_RATIO,
    COUNTING_LINE_COLOR,
    COUNTING_LINE_THICKNESS,
    DISPLAY_LABELS,
    CLASS_COLORS,
)


class VehicleCounter:
    """
    Stateful line-crossing counter.

    Tracks which vehicle IDs have already been counted so that a vehicle
    crossing the line multiple times is only counted once.

    Args:
        frame_height : pixel height of the video frame
        frame_width  : pixel width of the video frame (for drawing only)
        line_ratio   : vertical position of the counting line (0–1)
    """

    def __init__(
        self,
        frame_height: int,
        frame_width:  int,
        line_ratio:   float = COUNTING_LINE_RATIO,
    ) -> None:
        self.line_y: int = int(frame_height * line_ratio)
        self.frame_width = frame_width

        # Cumulative counts since the counter was created
        self._counts: Dict[str, int] = defaultdict(int)

        # Track IDs that have already crossed the line
        self._counted_ids: Set[int] = set()

        # Previous centroid Y per track ID (to detect direction of crossing)
        self._prev_cy: Dict[int, int] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, tracked: List[TrackedVehicle]) -> Dict[str, int]:
        """
        Process tracked vehicles for the current frame.

        Checks each vehicle's centroid against the counting line.
        Updates cumulative counts when a crossing is detected.

        Returns:
            Current cumulative counts dict: {"car": N, "bike": N, ...}
        """
        current_ids = {t.track_id for t in tracked}

        # Clean up stale centroid history for IDs no longer tracked
        stale = [tid for tid in self._prev_cy if tid not in current_ids]
        for tid in stale:
            del self._prev_cy[tid]

        for vehicle in tracked:
            tid = vehicle.track_id
            _, cy = vehicle.centroid

            if tid in self._counted_ids:
                # Already counted — just update previous position
                self._prev_cy[tid] = cy
                continue

            prev_cy = self._prev_cy.get(tid)

            if prev_cy is not None:
                # Check if centroid crossed the line between frames
                crossed = (
                    (prev_cy < self.line_y <= cy) or   # top → bottom
                    (prev_cy > self.line_y >= cy)       # bottom → top
                )
                if crossed:
                    self._counts[vehicle.class_name] += 1
                    self._counted_ids.add(tid)

            self._prev_cy[tid] = cy

        return dict(self._counts)

    @property
    def counts(self) -> Dict[str, int]:
        """Current cumulative counts (read-only snapshot)."""
        return dict(self._counts)

    @property
    def total(self) -> int:
        return sum(self._counts.values())

    def reset(self) -> None:
        """Reset all counts (e.g., between analysis windows)."""
        self._counts.clear()
        self._counted_ids.clear()
        self._prev_cy.clear()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_line(self, frame: np.ndarray) -> np.ndarray:
        """Draw the counting line and a label onto the frame (in-place)."""
        h, w = frame.shape[:2]
        cv2.line(
            frame,
            (0, self.line_y),
            (w, self.line_y),
            COUNTING_LINE_COLOR,
            COUNTING_LINE_THICKNESS,
        )
        cv2.putText(
            frame,
            "COUNT LINE",
            (10, self.line_y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            COUNTING_LINE_COLOR,
            1,
            cv2.LINE_AA,
        )
        return frame

    def draw_tracks(self, frame: np.ndarray, tracked: List[TrackedVehicle]) -> np.ndarray:
        """
        Draw bounding boxes, class labels, and track IDs onto the frame (in-place).
        """
        for vehicle in tracked:
            x1, y1, x2, y2 = vehicle.bbox
            color = CLASS_COLORS.get(vehicle.class_name, (200, 200, 200))
            label = DISPLAY_LABELS.get(vehicle.class_name, vehicle.class_name)

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label pill background
            text = f"{label} #{vehicle.track_id}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)

            # Label text
            cv2.putText(
                frame,
                text,
                (x1 + 3, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

            # Mark already-counted IDs with a dot on the centroid
            if vehicle.track_id in self._counted_ids:
                cx, cy = vehicle.centroid
                cv2.circle(frame, (cx, cy), 4, color, -1)

        return frame
