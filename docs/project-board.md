# Project Task Board & Issue Tracking

> GitHub Projects Board: **SIH'26 Urban Intelligence Development**  
> GitHub Issues Tracker: [github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence/issues](https://github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence/issues)

---

## Issue Status Summary

| Category | Total Tasks | Resolved (Closed) | In Progress / Open |
|---|---|---|---|
| **Traffic AI** | 3 | 3 | 0 |
| **Road AI (Potholes)** | 3 | 3 | 0 |
| **Backend & Database** | 5 | 5 | 0 |
| **Frontend & GIS** | 4 | 4 | 0 |
| **Edge & Integration** | 4 | 4 | 0 |
| **System Integration** | 4 | 3 | 1 |
| **Documentation & Submission** | 5 | 0 | 5 |
| **Total** | **28** | **22 Resolved** | **6 Open** |

---

## 1. Resolved Issues (22 Total)

The following tasks have been completed, verified with unit/smoke tests, and merged into `main`:

### Traffic AI — Owner: Pranav
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#1** | `[AI] Vehicle detection and classification prototype` | ✅ Closed | Implemented YOLOv8 vehicle detection & classification (`car`, `bike`, `bus`, `truck`) in [`edge-ai/traffic-detection/detector.py`](../edge-ai/traffic-detection/detector.py) with NMS and confidence thresholding. Merged via PR #29. |
| **#2** | `[AI] Vehicle counting logic` | ✅ Closed | Implemented SORT tracker with Kalman Filtering + Hungarian matching in [`edge-ai/traffic-detection/tracker.py`](../edge-ai/traffic-detection/tracker.py) and directional line-crossing counting in [`edge-ai/traffic-detection/counter.py`](../edge-ai/traffic-detection/counter.py). Merged via PR #29. |
| **#3** | `[AI] Traffic density estimation` | ✅ Closed | Implemented density level calculation (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), density score formulation, and HUD overlay in [`edge-ai/traffic-detection/density_estimator.py`](../edge-ai/traffic-detection/density_estimator.py). Merged via PR #29. |

### Road AI (Potholes) — Owner: Abhinandan
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#4** | `[ML] Select pothole dataset / model` | ✅ Closed | Selected YOLOv8 base architecture for road damage detection. Created local and cloud training scripts in [`edge-ai/Pothole_Road_Condition_Model/local_training/train_pothole.py`](../edge-ai/Pothole_Road_Condition_Model/local_training/train_pothole.py) and [`cloud_training/train_yolov8_kaggle.py`](../edge-ai/Pothole_Road_Condition_Model/cloud_training/train_yolov8_kaggle.py). Merged via PR #35 & #37. |
| **#5** | `[ML] Pothole detection prototype` | ✅ Closed | Developed standalone prototype detecting surface defects from video feeds in [`edge-ai/Pothole_Road_Condition_Model/pipeline.py`](../edge-ai/Pothole_Road_Condition_Model/pipeline.py) and multi-approach inference engines in [`edge_inference/`](../edge-ai/Pothole_Road_Condition_Model/edge_inference/). Merged via PR #35 & #37. |
| **#6** | `[ML] Confidence and severity scoring logic` | ✅ Closed | Implemented heuristic severity scoring (`low`, `medium`, `high`) based on bounding box width ratio to frame and spatial grid coverage. Integrated with pipeline in [`integration/run_pothole_pipeline.py`](../integration/run_pothole_pipeline.py). Merged via PR #35 & #37. |

### Backend & Database — Owner: Arjun
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#7** | `[BE] Design event database schema` | ✅ Closed | Designed and implemented SQLAlchemy relational DB schema (`Event`, `Bus`, `Hotspot`, `SystemAlert`) with automated SQLite/PostgreSQL migrations in [`backend/app/database.py`](../backend/app/database.py) and [`backend/app/models/`](../backend/app/models/). Merged via PR #30 & #32. |
| **#8** | `[BE] Implement POST /api/events` | ✅ Closed | Implemented `POST /api/events` endpoint in [`backend/app/routers/events.py`](../backend/app/routers/events.py) with Pydantic request validation, DB persistence, and automatic trigger for spatial hotspot clustering. Merged via PR #30 & #32. |
| **#9** | `[BE] Implement GET /api/events` | ✅ Closed | Implemented `GET /api/events` and `GET /api/events/{event_id}` in [`backend/app/routers/events.py`](../backend/app/routers/events.py) supporting query filters by `event_type`, `severity`, `status`, `bus_id`, limit, and offset pagination. Merged via PR #30 & #32. |
| **#10** | `[BE] Implement analytics endpoints` | ✅ Closed | Implemented aggregated analytics endpoints in [`backend/app/routers/analytics.py`](../backend/app/routers/analytics.py): `/analytics/summary`, `/analytics/traffic`, and `/analytics/road-conditions`. Merged via PR #30 & #32. |
| **#11** | `[BE] Implement GET /api/hotspots` | ✅ Closed | Implemented `GET /api/hotspots` in [`backend/app/routers/hotspots.py`](../backend/app/routers/hotspots.py) returning spatial clusters with confirmed detection counts and calculated priority scores. Merged via PR #30 & #32. |

### Frontend & GIS — Owner: Advika
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#12** | `[FE] Finalize dashboard from existing prototype` | ✅ Closed | Finalized responsive GIS dashboard layout with 6 core routes and deployed live on Vercel: [ai-powered-mobile-urban-intelligenc.vercel.app](https://ai-powered-mobile-urban-intelligenc.vercel.app/). |
| **#13** | `[FE] Connect GIS map to real event data` | ✅ Closed | Implemented dual-mode API consumer in [`frontend/src/services/api.js`](../frontend/src/services/api.js) and connected `GISMapPage.jsx` and `MiniMap.jsx` to live `GET /api/events` and `GET /api/hotspots` with fallback. Merged via PR #33 & #34. |
| **#14** | `[FE] Add event detail view (real data)` | ✅ Closed | Connected Event Management table (`EventPage.jsx`) and detail modal to live backend API with response normalization. Merged via PR #33 & #34. |
| **#15** | `[FE] Add analytics charts and heatmap (real data)` | ✅ Closed | Connected Traffic Analytics (`TrafficPage.jsx`) and Road Condition Analytics (`RoadConditionPage.jsx`) to backend aggregate endpoints with demo fallback. Merged via PR #33 & #34. |

### Edge & Integration — Owner: Parminder
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#16** | `[EDGE] Video input pipeline` | ✅ Closed | Implemented video input stream pipeline in [`edge-ai/traffic-detection/pipeline.py`](../edge-ai/traffic-detection/pipeline.py) and [`edge-ai/traffic-detection/run.py`](../edge-ai/traffic-detection/run.py) supporting webcam feeds (`0`), video files, frame rate control, and video exports. Merged via PR #29 & #31. |
| **#17** | `[EDGE] Event generator (AI -> schema)` | ✅ Closed | Implemented standardized `TrafficEvent` schema generation and JSON/JSONL serialization in [`edge-ai/traffic-detection/event_schema.py`](../edge-ai/traffic-detection/event_schema.py) and [`edge-ai/traffic-detection/pipeline.py`](../edge-ai/traffic-detection/pipeline.py). Merged via PR #29 & #31. |
| **#18** | `[EDGE] GPS simulation from CSV` | ✅ Closed | Implemented GPS trajectory simulation in [`integration/gps/gps_simulator.py`](../integration/gps/gps_simulator.py) reading synchronized timestamps and coordinates with 4+ decimal places from [`integration/gps/sample_route.csv`](../integration/gps/sample_route.csv). Merged via PR #31. |
| **#19** | `[EDGE] AI-to-backend HTTP integration` | ✅ Closed | Implemented HTTP client and edge event streamer in [`integration/event-generator/event_generator.py`](../integration/event-generator/event_generator.py) and [`integration/run_traffic_pipeline.py`](../integration/run_traffic_pipeline.py) with non-blocking POST requests, retries, and schema validation. Merged via PR #31. |

### System Integration — Owner: Team Lead
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#20** | `[INT] First end-to-end pipeline (Video -> Dashboard)` | ✅ Closed | Integrated and verified end-to-end data pipeline in [`integration/run_traffic_pipeline.py`](../integration/run_traffic_pipeline.py) and [`integration/test_pipeline.py`](../integration/test_pipeline.py): Video -> YOLOv8 / SORT -> Event Generator -> GPS Simulator -> Backend API (`POST /api/events`) -> SQLite DB. Merged via PR #31. |
| **#21** | `[INT] Persistent defect detection logic` | ✅ Closed | Implemented spatial clustering algorithm (50-meter Haversine distance threshold) in [`backend/app/services/hotspot_service.py`](../backend/app/services/hotspot_service.py) to identify persistent defects across multiple bus passes. Merged via PR #32. |
| **#22** | `[INT] Maintenance priority scoring` | ✅ Closed | Implemented maintenance priority formula in [`backend/app/services/hotspot_service.py`](../backend/app/services/hotspot_service.py) computing priority score from defect severity, confirmation count, and traffic density. Merged via PR #32. |

---

## 2. Active & Open Issues (6 Total)

The following tasks are active and scheduled for final testing and submission milestones:

### System Integration & Submission — Owner: Team Lead
| Issue | Task | Priority | Target Milestone | Description |
|---|---|---|---|---|
| **#23** | `[INT] Full system test` | High | Sept 8 | Execute end-to-end reliability stress testing across 15+ min continuous video streams and full synthetic dataset. |
| **#24** | `[DOC] Final README` | High | Sept 8 | Finalize repository documentation with complete module specifications, live URLs, and verification instructions. |
| **#25** | `[DOC] 6-page PPT` | High | Sept 9 | Create official SIH 6-page presentation slide deck in `presentation/`. |
| **#26** | `[DOC] Demo video with voiceover` | High | Sept 9 | Record and produce 3–5 min video walkthrough with voiceover in `demo/`. |
| **#27** | `[DOC] Full stack deployment` | High | Sept 9 | Deploy backend API and PostgreSQL database to cloud platform (Render / AWS) and link with Vercel frontend. |
| **#28** | `[DOC] Final repository audit` | High | Sept 10 | Perform final repository cleanup, security check, and submission rehearsal before deadline. |
