# Integration starter kit

Tested end-to-end and working. Drop these files straight into your repo
at the paths shown — they match your existing folder structure.

```
backend/
  api/
    main.py                      <- NEW (backend stub)
integration/
  event-generator/
    event_generator.py           <- NEW (the wrapper/glue script)
  gps/
    gps_simulator.py             <- NEW
    sample_route.csv             <- NEW
  test_pipeline.py               <- NEW
```

## 1. Install dependencies

From the repo root:

```
pip install fastapi "uvicorn[standard]" requests
```

(Add `fastapi`, `uvicorn[standard]`, `requests` to your root `requirements.txt`
so the rest of the team gets them too.)

## 2. Start the backend stub

```
cd backend/api
uvicorn main:app --reload --port 8000
```

Leave this running in its own terminal. Visit http://localhost:8000/api/events
in a browser — you should see `[]` (empty list, no events yet).

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

Once this stub (or Arjun's real backend) is running, tell Advika to update
`frontend/src/services/api.js` to `fetch()` from `http://localhost:8000/api/events`
instead of returning mock data.

## What's still a stub, not the real thing

- **Storage** is an in-memory Python list in `main.py` — it resets every
  time you restart the server. Swap this for SQLite/Postgres when Arjun's
  ready; the API contract (request/response shapes) won't need to change.
- **GPS** cycles through a hardcoded CSV route (`sample_route.csv`) near
  NSUT/Delhi. Replace with real GPS module output later.
- **Hotspot clustering** in `/api/hotspots` is a simple distance loop, fine
  for a demo but not built to scale past a few hundred events.
