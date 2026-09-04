# Integration starter kit

Tested end-to-end and working. Drop these files straight into your repo
at the paths shown — they match your existing folder structure.

```
backend/
  app/
    main.py                      <- FastAPI backend (models, routers, database)
integration/
  event-generator/
    event_generator.py           <- The wrapper/glue script
  gps/
    gps_simulator.py             <- GPS simulation
    sample_route.csv             <- Simulated GPS route points
  test_pipeline.py               <- Pipeline smoke test
```

## 1. Install dependencies

From the repo root:

```
pip install fastapi "uvicorn[standard]" requests
```

(Add `fastapi`, `uvicorn[standard]`, `requests` to your root `requirements.txt`
so the rest of the team gets them too.)

## 2. Start the backend

```
cd backend
uvicorn app.main:app --reload --port 8000
```

Leave this running in its own terminal. Visit http://localhost:8000/api/events
in a browser — you should see the stored events.

## 3. Run the pipeline smoke test

In a **second terminal**, from the repo root:

```
python integration/test_pipeline.py
```

You should see two `[sent]` lines and one `[skip]` (the fake low-confidence
detection, correctly discarded per the 0.65 threshold). Refresh
http://localhost:8000/api/events — the two sent events are now there.

## 4. Swap in Pranav's real model

Open `integration/test_pipeline.py` and replace `fake_traffic_detection()`
with a real call into Pranav's traffic AI function — as long as it returns
a dict with `event_type`, `confidence`, `severity`, `evidence`, nothing else
needs to change. Same for Abhinandan's pothole model when it's ready.

## 5. Point the frontend at it

The backend (`backend/app/main.py`) is fully database-backed and persistent with SQLite / PostgreSQL.
The frontend `frontend/src/services/api.js` connects to `http://localhost:8000` by default.

## What's still a stub, not the real thing

- **GPS** cycles through a hardcoded CSV route (`sample_route.csv`) near
  NSUT/Delhi. Replace with real GPS module output later.
- **Evidence frames**: Placeholder frame paths/indices can be swapped for S3/local file uploads.

