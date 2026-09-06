# Pothole AI Test & Verification Suite (`pothole-latest`)

This directory contains supplemental test suites (94 test cases) validating spatial deduplication, GPS coordinate boundary conditions, atomic cache persistence, and healing lifecycle logic.

## Contained Assets:
- `tests/` — 94 automated Pytest test cases (`test_detection.py`, `test_duplicates.py`, `test_gps.py`, `test_persistence.py`, `test_deletion.py`, `test_edge_cases.py`, `test_performance.py`, `test_event_id.py`, `test_end_to_end.py`).
- `Pothole_Road_Condition_Model/` — Local inference pipeline and cache manager.

## Primary Documentation:
- **Project Root README:** [`../README.md`](../README.md) (Primary authoritative source of truth)
- **Road AI Module Guide:** [`../edge-ai/pothole-detection/README.md`](../edge-ai/pothole-detection/README.md) & [`../docs/models/road-ai.md`](../docs/models/road-ai.md)
