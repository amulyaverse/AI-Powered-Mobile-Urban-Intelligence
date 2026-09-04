# Traffic AI / Vehicle Detection Module

> **Module Owner:** Pranav (Traffic AI / Computer Vision)  
> **Status:** ✅ Complete & Merged (PR #29)  
> **Location:** `edge-ai/traffic-detection/`

---

## Overview

The Traffic AI module processes raw video frames from bus-mounted cameras or live webcam feeds to detect, classify, track, and count vehicles in real time, while estimating road traffic density and streaming standardized JSON event snapshots.

---

## Architecture Pipeline

```
Video / Camera Feed
        ↓
  VehicleDetector         ← YOLOv8n pretrained on COCO (cars, bikes, buses, trucks)
        ↓
  VehicleTracker          ← SORT tracker (Kalman Filter + Hungarian Algorithm)
        ↓
  VehicleCounter          ← Directional line-crossing counter with persistent IDs
        ↓
  DensityEstimator        ← Active count + frame coverage ratio → LOW / MEDIUM / HIGH / CRITICAL
        ↓
  TrafficEvent (JSON)     ← Standardized JSON payload output (STDOUT / JSONL / API)
```

---

## Setup & Dependencies

```bash
# From project root
pip install -r edge-ai/traffic-detection/requirements.txt
```

### Core Libraries
- `ultralytics>=8.0.0` (YOLOv8 — auto-downloads pretrained weights `yolov8n.pt` ~6 MB on first run)
- `opencv-python>=4.8.0` (Video I/O, HUD overlay rendering)
- `filterpy>=1.4.5` & `scipy>=1.10.0` (Kalman Filter and Hungarian matching for SORT tracker)
- `numpy>=1.24.0`
- `torch>=2.0.0` & `torchvision>=0.15.0`

---

## Usage

### 1. Run on Live Webcam (Camera Index 0)
```bash
cd edge-ai/traffic-detection
python run.py --source 0 --show
```

### 2. Process a Video File with Live Window
```bash
python run.py --source /path/to/traffic.mp4 --show
```

### 3. Save Annotated Output Video
```bash
python run.py --source traffic.mp4 --show --save output.mp4
```

### 4. Headless Mode (Stream JSON Events to STDOUT)
```bash
python run.py --source traffic.mp4 --bus-id BUS-042
```

### 5. Stream Events to a JSONL File
```bash
python run.py --source traffic.mp4 --json-out events.jsonl
```

### CLI Parameters

| Flag | Default | Description |
|---|---|---|
| `--source`, `-s` | `0` | Camera index (e.g. `0` for webcam) or video file path |
| `--model`, `-m` | `yolov8n` | Model variant: `yolov8n`, `yolov8s`, `yolov8m`, `yolov8l`, `yolov8x` |
| `--conf`, `-c` | `0.40` | Detection confidence threshold |
| `--iou` | `0.45` | NMS IoU threshold |
| `--show` | `False` | Render OpenCV window with bounding boxes, tracks & HUD |
| `--save`, `-o` | `None` | Save annotated video file (MP4) |
| `--bus-id` | `BUS-001` | Bus identifier embedded in emitted events |
| `--emit-interval` | `1.0` | Event generation interval in seconds |
| `--json-out` | `None` | Output file for JSON Lines event stream |

---

## Classes & Density Mapping

### Vehicle Classes Detected
| Class | COCO Category ID |
|---|---|
| `car` | 2 |
| `bike` | 1 (bicycle), 3 (motorcycle) |
| `bus` | 5 |
| `truck` | 7 |

### Density Level Thresholds
| Density Level | Active Vehicles in Frame | Action / Alert State |
|---|---|---|
| `LOW` | 0 – 5 vehicles | Normal Flow |
| `MEDIUM` | 6 – 12 vehicles | Moderate Flow |
| `HIGH` | 13 – 20 vehicles | Heavy Traffic / Watchlist |
| `CRITICAL` | 21+ vehicles | Congestion Hotspot Triggered |

---

## Event Schema Integration

Emitted events conform to the platform event schema:

```json
{
  "event_type": "traffic_snapshot",
  "timestamp_iso": "2026-09-05T00:44:00Z",
  "bus_id": "BUS-042",
  "gps": { "lat": 28.6139, "lon": 77.2090 },
  "vehicle_counts": { "car": 18, "bike": 9, "bus": 2, "truck": 3 },
  "total_vehicles": 32,
  "density": "HIGH",
  "density_score": 0.78,
  "frame_coverage_ratio": 0.22,
  "confidence": 0.87,
  "source_frame": 450
}
```
