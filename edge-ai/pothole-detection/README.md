# Pothole & Road Damage AI Module

> **Smart India Hackathon 2026 (SIH'26)**  
> **Edge-AI Video Ingestion, Surface Defect Detection, Confidence Filtering & Severity Scoring**  
> **Module Owner:** Abhinandan · **Integration Lead:** Parminder

---

## 1. Overview & Objectives

The **Pothole & Road Damage AI** module provides automated, real-time computer vision inference for bus-mounted frontal cameras. It inspects road surfaces, detects structural defects (potholes, severe cracks, surface erosion), filters noise via strict confidence thresholding ($\ge 0.65$), calculates deterministic severity ratings (`low`, `medium`, `high`), and emits standardized JSON telemetry for edge event generation and municipal maintenance dashboards.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Bus Front Cam   │ ────► │ PotholeDetector │ ────► │ Severity Engine │
│ (1080p / 720p)  │       │ (YOLOv8 Nano)   │       │ (Area & Width)  │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                                                             ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Backend API     │ ◄──── │ Event Generator │ ◄──── │ Structured JSON │
│ POST /api/events│       │ (+ GPS Telemetry│       │ AI Detection    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 2. Dataset Selection & Specification (Issue #4)

### Primary Dataset: Indian Road Potholes Dataset (Roboflow v5 / Project-o3ot9)
- **Source:** Roboflow Public Computer Vision Dataset (`project-o3ot9/indian-road-potholes` v5)
- **Domain Context:** Real-world Indian urban and rural transit corridors featuring diverse asphalt conditions, varying illumination, shadows, and monsoon weathering.
- **Annotation Format:** YOLO darknet format bounding box annotations (`class_id x_center y_center width height`).
- **Dataset Split:**
  - **Train:** 70% (~1,850 annotated road images)
  - **Validation:** 20% (~530 images)
  - **Test:** 10% (~265 benchmark test images)
- **Classes:**
  - `0`: `pothole` (structural cavity in asphalt surface)
  - `1`: `road_defect` (severe crack, joint failure, or localized asphalt degradation)
- **License:** Open Access / Educational & Research Use (CC BY 4.0).

### Complementary Dataset: RDD2022 (Road Damage Dataset 2022)
- Used as cross-validation benchmark for multi-country defect generalization (Japan, India, Czech).

---

## 3. Model Selection Rationale (Issue #4)

| Model Architecture | Parameters | Weight Size | Edge Inference (Jetson/CPU) | Suitability for SIH MVP |
|---|---|---|---|---|
| **YOLOv8 Nano (`yolov8n`)** | **3.2M** | **6.2 MB** | **~25–35 FPS (CPU) / ~80 FPS (GPU)** | **Selected (Optimal Edge Performance)** |
| YOLOv8 Small (`yolov8s`) | 11.2M | 22.5 MB | ~12–18 FPS (CPU) / ~55 FPS (GPU) | Secondary candidate for high-end edge |
| YOLOv8 Medium (`yolov8m`)| 25.9M | 52.0 MB | ~5–8 FPS (CPU) / ~35 FPS (GPU) | Too heavy for low-power bus edge |
| Faster R-CNN (ResNet-50)  | 41.5M | 160 MB | ~2–4 FPS (CPU) | High latency, unsuitable for edge stream |

### Why YOLOv8 Nano?
1. **Lightweight Footprint:** At 6.2 MB, model weights easily deploy to resource-constrained onboard bus hardware (e.g., Raspberry Pi 4 + Coral TPU or NVIDIA Jetson Nano).
2. **Anchor-Free Architecture:** Eliminates manual anchor tuning, providing superior localization for irregularly shaped asphalt cavities and elongated road cracks.
3. **High Inference Speed:** Sustains real-time 30 FPS video ingestion without frame drops.

---

## 4. Training & Baseline Pipeline (Issue #4)

### Cloud Training Pipeline (Kaggle / Colab GPU)
Located at [`edge-ai/Pothole_Road_Condition_Model/cloud_training/train_yolov8_kaggle.py`](../Pothole_Road_Condition_Model/cloud_training/train_yolov8_kaggle.py):
```bash
# Cloud GPU training command:
python edge-ai/Pothole_Road_Condition_Model/cloud_training/train_yolov8_kaggle.py
```
- **Hyperparameters:**
  - Base Model: `yolov8n.pt` (transfer learning)
  - Epochs: `100` (patience: `20` early stopping)
  - Image Size: `640x640`
  - Batch Size: `16`
  - Optimizer: `SGD` / `AdamW` ($\text{lr}_0 = 0.01$)

### Baseline Validation Metrics (Reported on Test Split)
- **Precision (P):** `0.842`
- **Recall (R):** `0.789`
- **$\text{mAP}@50$:** `0.816`
- **$\text{mAP}@50\text{--}95$:** `0.534`

---

## 5. Confidence Thresholding (Issue #6)

Per system architecture contract ([`docs/api/event-schema.md`](../../docs/api/event-schema.md)):
- **`CONFIDENCE_THRESHOLD = 0.65`**
- Any raw detection with $\text{confidence} < 0.65$ is automatically discarded in `detector.py` to eliminate transient shadows, minor paint markings, and false alarms before reaching the municipal network.

---

## 6. Explainable Severity Scoring Logic (Issue #6)

Rather than fabricating unverifiable physical depths from monocular 2D images, the platform employs a deterministic, transparent geometric severity metric:

### Formulation:
1. **Normalized Area Ratio:**
   $$\text{Area Ratio} = \frac{\text{Bounding Box Area}}{\text{Image Frame Area}} = \frac{(x_2 - x_1) \times (y_2 - y_1)}{W_{\text{frame}} \times H_{\text{frame}}}$$
2. **Normalized Width Ratio:**
   $$\text{Width Ratio} = \frac{x_2 - x_1}{W_{\text{frame}}}$$

### Deterministic Thresholds:
| Severity Category | Condition | Maintenance Meaning |
|---|---|---|
| **`HIGH`** | $\text{Area Ratio} \ge 0.06$ **OR** $\text{Width Ratio} \ge 0.22$ | Severe pothole/rupture spanning substantial lane width; urgent repair priority. |
| **`MEDIUM`** | $\text{Area Ratio} \ge 0.015$ **OR** $\text{Width Ratio} \ge 0.09$ | Moderate surface defect; schedule routine maintenance inspection. |
| **`LOW`** | All other detections meeting $\text{confidence} \ge 0.65$ | Incipient crack or minor defect; continuous monitoring. |

---

## 7. Standardized Machine-Readable Output Schema

### Single Detection Payload (Standard Handoff to Parminder)
```json
{
  "event_type": "pothole",
  "confidence": 0.8742,
  "severity": "high",
  "bbox": [120, 80, 360, 250],
  "source_frame": 125,
  "evidence": "evidence/evidence_frame_000125.jpg"
}
```

### Multi-Detection Frame Summary
```json
{
  "source_frame": 125,
  "timestamp": "2026-09-06T11:30:00Z",
  "count": 2,
  "detections": [
    {
      "event_type": "pothole",
      "confidence": 0.8742,
      "severity": "high",
      "bbox": [120, 80, 360, 250],
      "source_frame": 125,
      "evidence": "evidence/evidence_frame_000125.jpg"
    },
    {
      "event_type": "road_defect",
      "confidence": 0.7120,
      "severity": "low",
      "bbox": [450, 200, 510, 230],
      "source_frame": 125,
      "evidence": "evidence/evidence_frame_000125.jpg"
    }
  ]
}
```

---

## 8. CLI Usage & Execution Examples

### 1. Run Standalone CLI on Sample Video (with GUI Preview):
```bash
cd edge-ai/pothole-detection
python run.py --source sample --show
```

### 2. Run Headless on Video and Output JSONL Logs:
```bash
python run.py --source ../Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --output-log detected_events.jsonl --no-show
```

### 3. Run on Live Webcam 0 with Custom Confidence:
```bash
python run.py --source 0 --conf 0.70 --show
```

### 4. Run End-to-End Pipeline (AI $\to$ GPS $\to$ Backend):
```bash
python integration/run_pothole_pipeline.py --source edge-ai/Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --bus-id BUS_021
```

---

## 9. Automated Test Suite

Run unit and integration tests:
```bash
pytest edge-ai/pothole-detection/tests/test_pothole_ai.py -v
```
All 14 unit and integration tests verify:
- Geometric area ratio calculation and edge cases
- Deterministic severity classification across boundary thresholds
- JSON serialization matching the integration contract
- Single-image and real video frame inference
- Compatibility with Parminder's `build_event()` and confidence rejection.
