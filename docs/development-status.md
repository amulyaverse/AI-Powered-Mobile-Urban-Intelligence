# Development Status

> Last updated: 5 September 2026. Update this file as module status changes.

| Module | Owner | Status | Next Deliverable |
|--------|-------|--------|-----------------|
| Traffic AI | Pranav | ✅ Complete | Benchmarking & video pipeline integration (PR #29 merged) |
| Road AI | Abhinandan | 🟡 In Progress | Pothole detection model running on sample images |
| Backend | Arjun | 🔵 Planned | Events API (`POST` + `GET /api/events`) |
| Frontend / GIS | Advika | ✅ Complete | Prepare API integration (replace mock data) |
| Edge / Integration | Parminder | 🟡 In Progress | Video stream + event pipeline integration |
| System Integration | Team Lead | 🟡 In Progress | Architecture, end-to-end integration & submission |

---

## Status Key

| Icon | Meaning |
|------|---------|
| ✅ | Complete / working |
| 🟡 | In progress |
| 🔵 | Planned — not started |
| 🔴 | Blocked |

---

## Traffic AI (Vehicle Detection Pipeline)

The Vehicle AI pipeline is **complete and merged** (PR #29).

- **Implementation Location:** `edge-ai/traffic-detection/`
- **Full Specs:** See [`docs/models/traffic-ai.md`](models/traffic-ai.md)
- **Features Implemented:**
  - YOLOv8 vehicle detection & classification (`car`, `bike`, `bus`, `truck`) in `detector.py`
  - SORT tracker with Kalman Filtering + Hungarian matching in `tracker.py`
  - Directional line-crossing counting in `counter.py`
  - Real-time traffic density estimation (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) in `density_estimator.py`
  - Standardized JSON `TrafficEvent` snapshot generation in `event_schema.py`
  - CLI runner supporting webcam, video files, headless mode, and video export in `run.py`

**Next step for Pranav:** Run benchmark evaluations on recorded bus video clips and assist Parminder with multi-model edge integration.

---

## Frontend / GIS Platform

The React/Vite frontend prototype is **complete and deployed**.

- **Live URL:** https://ai-powered-mobile-urban-intelligenc.vercel.app/
- **State:** Running on mock data representing the final JSON event schema.
- **Routes:** Overview, Live Monitoring, Events & Incidents, GIS Map, Traffic Analytics, Road Analytics.
- **Service Layer:** `frontend/src/services/api.js` ready to swap mock data with backend API endpoints.

**Next step for Advika:** When the backend API is ready, point `src/services/api.js` to `VITE_API_BASE_URL`.

---

## Road AI (Pothole & Defect Detection)

**Next steps for Abhinandan:**
1. Choose and benchmark pothole/road damage dataset (RDD2022 / Pothole-600)
2. Train/fine-tune detection model in `edge-ai/pothole-detection/`
3. Compute severity estimate from bounding box area and confidence
4. Output standard event dictionary matching `docs/api/event-schema.md`

---

## Backend & Database

**Next steps for Arjun:**
1. Set up FastAPI project in `backend/api/`
2. Implement event database schema (PostgreSQL / SQLite) based on `docs/api/event-schema.md`
3. Implement `POST /api/events` and `GET /api/events`
4. Add spatial clustering logic for persistent defect hotspots (`GET /api/hotspots`)
5. Enable CORS headers for frontend integration

---

## Edge & Integration

**Next steps for Parminder:**
1. Connect Traffic AI (`edge-ai/traffic-detection/pipeline.py`) and upcoming Road AI into unified edge runner
2. Attach simulated GPS coordinates from CSV trace
3. Send generated events via HTTP `POST /api/events` to Arjun's backend
