# Integration Layer & End-to-End Pipeline

> **Module Owner:** Parminder (Edge AI / Integration)  
> **Status:** ✅ Tested & Working (PR #31)  
> **Source Directory:** `integration/`

---

## Architecture Overview

The integration layer acts as the glue connecting Edge AI models, GPS telemetry simulation, and the Central Backend API:

```
[Video Feed / Camera]
        ↓
[Edge AI: Vehicle / Pothole Detection] (Returns detection dict + confidence)
        ↓
[GPS Simulator: integration/gps/gps_simulator.py] (Syncs lat/lon from route CSV)
        ↓
[Event Generator: integration/event-generator/event_generator.py] (Enforces >=0.65 conf threshold, UUID, UTC timestamp)
        ↓
[HTTP Client: POST /api/events]
        ↓
[Backend FastAPI: backend/app/main.py] (Stores in SQLite / PostgreSQL + checks spatial clusters)
```

---

## Directory Structure

```
integration/
├── event-generator/
│   └── event_generator.py        # Wraps raw AI detections into standardized Event payloads
├── gps/
│   ├── gps_simulator.py          # Coordinates simulation from waypoint trace
│   └── sample_route.csv          # Sample Delhi route waypoints (lat, lon, speed)
├── run_traffic_pipeline.py       # Live runner connecting YOLOv8 detection -> GPS -> Backend
└── test_pipeline.py              # End-to-end smoke test script
```

---

## Running the End-to-End Pipeline

### Step 1: Start the Backend Server
In Terminal 1:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger API docs available at: **http://localhost:8000/docs**

### Step 2: Run the Traffic AI Pipeline with Live Backend Streaming
In Terminal 2:
```bash
python integration/run_traffic_pipeline.py --source 0 --backend-url http://localhost:8000/api/events --bus-id BUS-001
```

Or run the pipeline smoke test:
```bash
python integration/test_pipeline.py
```

---

## GPS Simulation
- The simulator reads coordinates from `integration/gps/sample_route.csv` (Delhi/NSUT route points).
- Emits coordinates with 4+ decimal places and calculates simulated speeds and headings.
- Ready to be swapped with serial USB NMEA GPS hardware stream when deployed on physical buses.
