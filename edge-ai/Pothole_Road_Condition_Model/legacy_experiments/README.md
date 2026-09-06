# Legacy Pothole Detection Experiments

This directory contains the original prototype and experimental scripts authored during early development (commit `c48aa69`, PR #35).

## Contained Files:
- `detect_potholes.py` — Original OpenCV + YOLOv8 visual inference script with desktop GUI window (`cv2.imshow`).
- `detect_potholes_low_spec.py` — Low-spec device optimization prototype with frame skipping and reduced resolution.
- `merge_datasets.py` — Dataset merging and YAML preparation script.
- `pothole_train.py` — Initial training entry point using YOLOv8n.

## Active Modular Architecture:
For the production-grade, integration-ready modular pipeline, please refer to:
- [`edge-ai/pothole-detection/`](../pothole-detection/) — Canonical modular package with automated geometric severity grading (`pothole_severity.py`), dataclass JSON serialization (`pothole_event_schema.py`), frame generator (`pothole_pipeline.py`), and test suite (`tests/test_pothole_ai.py`).
- [`edge-ai/Pothole_Road_Condition_Model/`](../Pothole_Road_Condition_Model/) — Training scripts and edge inference engines (Approach A & B).
- [`integration/run_pothole_pipeline.py`](../../integration/run_pothole_pipeline.py) — End-to-end integration runner streaming pothole events directly to the FastAPI backend.
