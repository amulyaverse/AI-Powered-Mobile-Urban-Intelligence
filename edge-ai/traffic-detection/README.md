# edge-ai/traffic-detection — Vehicle AI Module

> **Member 1 — Vehicle AI / Computer Vision**  
> **Branch:** `feature/member1-vehicle-ai`  
> **SIH 2026**

---

## What This Module Does

Takes a video (or live camera feed) as input and outputs:

```
Cars: 18 | Bikes: 9 | Buses: 2 | Trucks: 3 | Total: 32 | Density: HIGH | Conf: 0.87
```

Plus a structured JSON event every second:

```json
{
  "event_type": "traffic_snapshot",
  "timestamp_iso": "2026-09-03T00:44:00",
  "bus_id": "BUS-042",
  "gps": { "lat": 12.9716, "lon": 77.5946 },
  "vehicle_counts": { "car": 18, "bike": 9, "bus": 2, "truck": 3 },
  "total_vehicles": 32,
  "density": "HIGH",
  "density_score": 0.78,
  "frame_coverage_ratio": 0.22,
  "confidence": 0.87,
  "source_frame": 450
}
```

---

## Architecture

```
Video / Camera Feed
        ↓
  VehicleDetector         ← YOLOv8n pretrained on COCO
        ↓
  VehicleTracker          ← SORT (Kalman + Hungarian, CPU-only)
        ↓
  VehicleCounter          ← Line-crossing, unique ID per vehicle
        ↓
  DensityEstimator        ← Count + coverage → LOW/MEDIUM/HIGH/CRITICAL
        ↓
  TrafficEvent (JSON)     ← Output to backend / stdout / JSONL file
```

---

## Setup

```bash
cd edge-ai/traffic-detection
pip install -r requirements.txt
```

> **Note:** YOLOv8 weights (`yolov8n.pt`, ~6 MB) are **auto-downloaded** on first run. No manual download needed.

---

## Usage

### Basic — process a video file

```bash
python run.py --source path/to/traffic.mp4 --show
```

### Save annotated output video

```bash
python run.py --source traffic.mp4 --show --save output.mp4
```

### Webcam (camera index 0)

```bash
python run.py --source 0 --show
```

### Headless (no window) — just print events

```bash
python run.py --source traffic.mp4
```

### Save events to JSONL file

```bash
python run.py --source traffic.mp4 --json-out events.jsonl
```

### Use a larger model for better accuracy

```bash
python run.py --source traffic.mp4 --model yolov8m --show
```

### Full options

```
  --source / -s     Video file path or camera index   (default: 0)
  --model  / -m     yolov8n | yolov8s | yolov8m | yolov8l | yolov8x
  --conf   / -c     Detection confidence threshold    (default: 0.40)
  --iou             NMS IoU threshold                 (default: 0.45)
  --show            Display annotated window
  --save            Save annotated video to file
  --bus-id          Bus identifier for events         (default: BUS-001)
  --emit-interval   Emit event every N seconds        (default: 1.0)
  --json-out        Write events as JSONL to file
```

---

## Vehicle Classes Detected

| Class | COCO IDs Used |
|-------|--------------|
| `car` | 2 |
| `bike` | 1 (bicycle) + 3 (motorcycle) |
| `bus` | 5 |
| `truck` | 7 |

---

## Density Levels

| Level | Vehicles in Frame |
|-------|------------------|
| LOW | 0 – 5 |
| MEDIUM | 6 – 12 |
| HIGH | 13 – 20 |
| CRITICAL | 21+ |

Thresholds are configurable in [`config.py`](config.py).

---

## Running Tests

```bash
cd edge-ai/traffic-detection
python -m pytest tests/ -v
```

Tests cover: detector, counter (line-crossing logic), density estimator, and TrafficEvent schema. **No video file needed** — tests use synthetic frames and mock data.

---

## File Structure

```
edge-ai/traffic-detection/
├── config.py              # All thresholds, model name, class mappings
├── detector.py            # YOLOv8 wrapper → Detection objects
├── tracker.py             # SORT tracker → TrackedVehicle objects
├── counter.py             # Line-crossing counter → class counts
├── density_estimator.py   # Count + coverage → density label + score
├── event_schema.py        # TrafficEvent dataclass (JSON output)
├── pipeline.py            # Main orchestrator
├── run.py                 # CLI entry point
├── requirements.txt       # Dependencies
├── README.md              # This file
└── tests/
    ├── test_detector.py
    ├── test_counter.py
    └── test_density.py
```

---

## Integration with Backend (Member 3)

This module outputs `TrafficEvent` objects. To send them to the backend:

```python
from pipeline import TrafficPipeline
import requests

pipeline = TrafficPipeline(source="traffic.mp4", bus_id="BUS-042")

for event in pipeline.run():
    requests.post("http://backend-api/events/traffic", json=event.to_dict())
```

---

## Model Comparison (Speed vs Accuracy)

| Model | Size | Speed (CPU) | mAP |
|-------|------|------------|-----|
| yolov8n | 6 MB | ~30 fps | Good |
| yolov8s | 22 MB | ~20 fps | Better |
| yolov8m | 52 MB | ~12 fps | Best for laptop |
| yolov8l | 87 MB | ~7 fps | High accuracy |

**Recommended for edge device (Raspberry Pi / Jetson):** `yolov8n`  
**Recommended for laptop testing:** `yolov8m`
