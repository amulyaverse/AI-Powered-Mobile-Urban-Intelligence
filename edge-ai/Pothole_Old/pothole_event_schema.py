"""
pothole_event_schema.py
-----------------------
Standardized dataclasses and serialization schemas for Pothole AI outputs.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import json


@dataclass
class PotholeDetection:
    bbox: Tuple[int, int, int, int]
    class_name: str
    confidence: float
    severity: str
    area_ratio: float = 0.0
    source_frame: int = 0
    evidence: str = ""

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def area(self) -> int:
        x1, y1, x2, y2 = self.bbox
        return max(0, x2 - x1) * max(0, y2 - y1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.class_name,
            "confidence": round(self.confidence, 4),
            "severity": self.severity,
            "bbox": [int(v) for v in self.bbox],
            "source_frame": int(self.source_frame),
            "evidence": self.evidence,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class PotholeFrameSummary:
    source_frame: int
    detections: List[PotholeDetection]
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_frame": self.source_frame,
            "timestamp": self.timestamp,
            "count": len(self.detections),
            "detections": [d.to_dict() for d in self.detections],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
