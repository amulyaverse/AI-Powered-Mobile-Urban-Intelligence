# Project Task Board & Issue Tracking

> GitHub Projects Board: **SIH'26 Urban Intelligence Development**  
> GitHub Issues Tracker: [github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence/issues](https://github.com/amulyaverse/AI-Powered-Mobile-Urban-Intelligence/issues)

---

## Issue Status Summary

| Category | Total Tasks | Resolved (Closed) | In Progress / Open |
|---|---|---|---|
| **Traffic AI** | 3 | 3 | 0 |
| **Road AI (Potholes)** | 3 | 0 | 3 |
| **Backend & Database** | 5 | 5 | 0 |
| **Frontend & GIS** | 4 | 1 | 3 |
| **Edge & Integration** | 4 | 4 | 0 |
| **System Integration** | 4 | 3 | 1 |
| **Documentation & Submission** | 5 | 0 | 5 |
| **Total** | **28** | **16 Resolved** | **12 Open** |

---

## 1. Resolved Issues

The following tasks have been completed, verified with unit/smoke tests, and merged into `main`:

### Traffic AI — Owner: Pranav
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#1** | `[AI] Vehicle detection and classification prototype` | ✅ Closed | Implemented YOLOv8 vehicle detection & classification (`car`, `bike`, `bus`, `truck`) in [`edge-ai/traffic-detection/detector.py`](../edge-ai/traffic-detection/detector.py) with NMS and confidence thresholding. |
| **#2** | `[AI] Vehicle counting logic` | ✅ Closed | Implemented SORT tracker with Kalman Filtering + Hungarian matching in [`edge-ai/traffic-detection/tracker.py`](../edge-ai/traffic-detection/tracker.py) and directional line-crossing counting in [`edge-ai/traffic-detection/counter.py`](../edge-ai/traffic-detection/counter.py). |
| **#3** | `[AI] Traffic density estimation` | ✅ Closed | Implemented density level calculation (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), density score formulation, and HUD overlay in [`edge-ai/traffic-detection/density_estimator.py`](../edge-ai/traffic-detection/density_estimator.py). |

### Backend & Database — Owner: Arjun
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#7** | `[BE] Design event database schema` | ✅ Closed | Designed and implemented SQLAlchemy relational DB schema (`Event`, `Bus`, `Hotspot`, `SystemAlert`) with automated SQLite/PostgreSQL migrations in [`backend/app/database.py`](../backend/app/database.py) and [`backend/app/models/`](../backend/app/models/). |
| **#8** | `[BE] Implement POST /api/events` | ✅ Closed | Implemented `POST /api/events` endpoint in [`backend/app/routers/events.py`](../backend/app/routers/events.py) with Pydantic request validation, DB persistence, and automatic trigger for spatial hotspot clustering. |
| **#9** | `[BE] Implement GET /api/events` | ✅ Closed | Implemented `GET /api/events` and `GET /api/events/{event_id}` in [`backend/app/routers/events.py`](../backend/app/routers/events.py) supporting query filters by `event_type`, `severity`, `status`, `bus_id`, limit, and offset pagination. |
| **#10** | `[BE] Implement analytics endpoints` | ✅ Closed | Implemented aggregated analytics endpoints in [`backend/app/routers/analytics.py`](../backend/app/routers/analytics.py): `/analytics/summary`, `/analytics/traffic`, and `/analytics/road-conditions`. |
| **#11** | `[BE] Implement GET /api/hotspots` | ✅ Closed | Implemented `GET /api/hotspots` in [`backend/app/routers/hotspots.py`](../backend/app/routers/hotspots.py) returning spatial clusters with confirmed detection counts and calculated priority scores. |

### Edge & Integration — Owner: Parminder
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#16** | `[EDGE] Video input pipeline` | ✅ Closed | Implemented video input stream pipeline in [`edge-ai/traffic-detection/pipeline.py`](../edge-ai/traffic-detection/pipeline.py) and [`edge-ai/traffic-detection/run.py`](../edge-ai/traffic-detection/run.py) supporting webcam feeds (`0`), video files, frame rate control, and video exports. |
| **#17** | `[EDGE] Event generator (AI -> schema)` | ✅ Closed | Implemented standardized `TrafficEvent` schema generation and JSON/JSONL serialization in [`edge-ai/traffic-detection/event_schema.py`](../edge-ai/traffic-detection/event_schema.py) and [`edge-ai/traffic-detection/pipeline.py`](../edge-ai/traffic-detection/pipeline.py). |
| **#18** | `[EDGE] GPS simulation from CSV` | ✅ Closed | Implemented GPS trajectory simulation in [`integration/gps/gps_simulator.py`](../integration/gps/gps_simulator.py) reading synchronized timestamps and coordinates with 4+ decimal places from [`integration/gps/sample_route.csv`](../integration/gps/sample_route.csv). |
| **#19** | `[EDGE] AI-to-backend HTTP integration` | ✅ Closed | Implemented HTTP client and edge event streamer in [`integration/event-generator/event_generator.py`](../integration/event-generator/event_generator.py) and [`integration/run_traffic_pipeline.py`](../integration/run_traffic_pipeline.py) with non-blocking POST requests, retries, and schema validation. |

### System Integration — Owner: Team Lead
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#20** | `[INT] First end-to-end pipeline (Video -> Dashboard)` | ✅ Closed | Integrated and verified end-to-end data pipeline in [`integration/run_traffic_pipeline.py`](../integration/run_traffic_pipeline.py) and [`integration/test_pipeline.py`](../integration/test_pipeline.py): Video -> YOLOv8 / SORT -> Event Generator -> GPS Simulator -> Backend API (`POST /api/events`) -> SQLite DB. |
| **#21** | `[INT] Persistent defect detection logic` | ✅ Closed | Implemented spatial clustering algorithm (50-meter Haversine distance threshold) in [`backend/app/services/hotspot_service.py`](../backend/app/services/hotspot_service.py) to identify persistent defects across multiple bus passes. |
| **#22** | `[INT] Maintenance priority scoring` | ✅ Closed | Implemented maintenance priority formula in [`backend/app/services/hotspot_service.py`](../backend/app/services/hotspot_service.py) computing priority score from defect severity, confirmation count, and traffic density. |

### Frontend — Owner: Advika
| Issue | Task | Status | Resolution Description & Source Code |
|---|---|---|---|
| **#12** | `[FE] Finalize dashboard from existing prototype` | ✅ Closed | Finalized responsive GIS dashboard layout with 6 core routes and deployed live on Vercel: [ai-powered-mobile-urban-intelligenc.vercel.app](https://ai-powered-mobile-urban-intelligenc.vercel.app/). |

---

## 2. Active & Open Issues

The following tasks are active and scheduled for upcoming development milestones:

### Road AI — Owner: Abhinandan
| Issue | Task | Priority | Description |
|---|---|---|---|
| **#4** | `[ML] Select pothole dataset / model` | High | Select and benchmark pothole/road damage dataset (RDD2022 / Pothole-600) and model architecture. |
| **#5** | `[ML] Pothole detection prototype` | High | Develop standalone prototype detecting potholes and major road defects from surface imagery. |
| **#6** | `[ML] Confidence and severity scoring logic` | Medium | Implement heuristic scoring to assign categorical severity (`low`, `medium`, `high`, `critical`). |

### Frontend & GIS Integration — Owner: Advika
| Issue | Task | Priority | Description |
|---|---|---|---|
| **#13** | `[FE] Connect GIS map to real event data` | High | Wire `GISMapPage` and `MiniMap` to consume live events and hotspots from `GET /api/events` and `GET /api/hotspots`. |
| **#14** | `[FE] Add event detail view (real data)` | Medium | Connect Event Management table and Detail Modal to live backend API. |
| **#15** | `[FE] Add analytics charts and heatmap (real data)` | Medium | Connect Traffic Analytics and Road Condition Analytics pages to backend aggregate endpoints. |

### System Integration & Submission — Owner: Team Lead
| Issue | Task | Priority | Description |
|---|---|---|---|
| **#23** | `[INT] Full system test` | High | Execute end-to-end reliability testing across continuous video streams and full dataset. |
| **#24** | `[DOC] Final README` | High | Finalize documentation with model accuracy benchmarks, live URLs, and demo embeds. |
| **#25** | `[DOC] 6-page PPT` | High | Create official SIH 6-page presentation deck. |
| **#26** | `[DOC] Demo video with voiceover` | High | Record and produce 3–5 min video walkthrough with voiceover. |
| **#27** | `[DOC] Full stack deployment` | High | Deploy backend API and database to cloud platform (Render / AWS) and link with Vercel frontend. |
| **#28** | `[DOC] Final repository audit` | High | Perform final repository cleanup and compliance audit before deadline. |
