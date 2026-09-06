# Road Damage & Pothole AI Module

> **Module Owner:** Abhinandan (Road Damage AI / Computer Vision)  
> **Status:** ✅ Complete & Verified (Issues #4, #5, #6)  
> **Location:** `edge-ai/pothole-detection/` & `edge-ai/Pothole_Road_Condition_Model/`

---

## Overview

The Road Damage AI module analyzes video feeds from bus-mounted forward-facing cameras to detect potholes, severe road cracks, and surface cavities in real time. It filters detections against a strict confidence threshold ($\ge 0.65$), applies deterministic geometric severity scoring (`low`, `medium`, `high`), and emits standardized JSON telemetry directly into the edge integration pipeline.

---

## Architecture Pipeline

```
Video / Camera Feed
        ↓
  PotholeDetector         ← YOLOv8n (optimized for edge inference)
        ↓
  Confidence Filter       ← Discards detections below threshold (conf < 0.65)
        ↓
  Severity Engine         ← Relative area ratio + width ratio → LOW / MEDIUM / HIGH
        ↓
  Evidence Capture        ← Saves annotated bounding box frame
        ↓
  PotholeDetection (JSON) ← Standardized machine-readable dictionary payload
        ↓
  EventGenerator          ← Attaches GPS, UTC timestamp, Bus ID, Camera ID
        ↓
  FastAPI Backend         ← POST /api/events (triggers 50m spatial clustering)
```

---

## Setup & Dependencies

```bash
# From project root
pip install -r edge-ai/pothole-detection/requirements.txt
```

### Core Libraries
- `ultralytics>=8.0.0` (YOLOv8 — auto-downloads lightweight weights `yolov8n.pt` ~6.2 MB)
- `opencv-python>=4.8.0` (Video ingestion, frame extraction, HUD bounding box rendering)
- `numpy>=1.24.0` (Array and geometry operations)
- `torch>=2.0.0` (PyTorch 2.6+ safe weight loading)
- `pytest>=7.0.0` (Automated testing suite)

---

## Usage

### 1. Run Standalone CLI with Live Preview
```bash
cd edge-ai/pothole-detection
python run.py --source sample --show
```

### 2. Process Video File Headless and Log JSONL
```bash
python run.py --source ../Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --output-log events.jsonl --no-show
```

### 3. Run End-to-End Live Streamer (AI $\to$ GPS $\to$ Backend)
```bash
# With FastAPI backend running at localhost:8000:
python integration/run_pothole_pipeline.py --source edge-ai/Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --bus-id BUS_021
```

---

## Dataset & Training Specification

- **Dataset:** Roboflow Indian Road Potholes v5 (`project-o3ot9/indian-road-potholes`)
- **Classes:** `pothole` (0), `road_defect` (1)
- **Model:** YOLOv8 Nano (3.2M parameters, 6.2 MB)
- **Evaluation Metrics (on Test Split):**
  - Precision: `0.842`
  - Recall: `0.789`
  - mAP@50: `0.816`
  - mAP@50-95: `0.534`

---

## Explainable Severity Formulation

$$\text{Area Ratio} = \frac{\text{Bounding Box Area}}{\text{Image Frame Area}}$$
$$\text{Width Ratio} = \frac{\text{Bounding Box Width}}{\text{Image Frame Width}}$$

- **HIGH:** $\text{Area Ratio} \ge 0.06$ **OR** $\text{Width Ratio} \ge 0.22$
- **MEDIUM:** $\text{Area Ratio} \ge 0.015$ **OR** $\text{Width Ratio} \ge 0.09$
- **LOW:** Remaining detections with $\text{confidence} \ge 0.65$
