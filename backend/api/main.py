"""
Minimal backend API stub for the Urban Sensing platform.
Matches the event schema in docs/api/event-schema.md exactly.

This exists so Traffic AI -> Integration -> Dashboard can be tested
end-to-end right now, without waiting on the real database-backed
API. Swap the in-memory EVENTS list for SQLite/Postgres later --
the request/response contract below doesn't need to change.

Run from the backend/api/ folder:
    uvicorn main:app --reload --port 8000
"""

import math
import uuid
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Urban Sensing Events API")

# Allow the Vite frontend (localhost:5173) to call this during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- In-memory "database" (replace with SQLite/Postgres later) ----
EVENTS: List[dict] = []

ALLOWED_EVENT_TYPES = {"pothole", "road_defect", "congestion", "vehicle_count"}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}


class EventIn(BaseModel):
    event_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str
    bus_id: str
    camera_id: str
    latitude: float
    longitude: float
    timestamp: str
    evidence: str
    # event_id / status are optional on input -- backend assigns them
    # if the integration layer didn't already set them
    event_id: Optional[str] = None
    status: Optional[str] = "new"


@app.post("/api/events", status_code=201)
def create_event(event: EventIn):
    if event.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(400, f"invalid event_type: {event.event_type}")
    if event.severity not in ALLOWED_SEVERITIES:
        raise HTTPException(400, f"invalid severity: {event.severity}")

    record = event.dict()
    record["event_id"] = record["event_id"] or f"EVT_{uuid.uuid4().hex[:8]}"
    record["status"] = record["status"] or "new"
    EVENTS.append(record)
    return record


@app.get("/api/events")
def list_events(
    event_type: Optional[str] = Query(None),
    bus_id: Optional[str] = Query(None),
):
    results = EVENTS
    if event_type:
        results = [e for e in results if e["event_type"] == event_type]
    if bus_id:
        results = [e for e in results if e["bus_id"] == bus_id]
    return results


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    for e in EVENTS:
        if e["event_id"] == event_id:
            return e
    raise HTTPException(404, "event not found")


@app.get("/api/analytics/summary")
def analytics_summary():
    by_type: dict = {}
    by_severity: dict = {}
    for e in EVENTS:
        by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
        by_severity[e["severity"]] = by_severity.get(e["severity"], 0) + 1
    return {"total_events": len(EVENTS), "by_type": by_type, "by_severity": by_severity}


def _haversine_m(lat1, lon1, lat2, lon2):
    """Distance in metres between two lat/long points."""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@app.get("/api/hotspots")
def hotspots(radius_m: float = 50.0, min_reports: int = 2):
    """
    Groups defect events (pothole / road_defect) that fall within
    radius_m metres of each other -- a simple stand-in for the real
    persistent-detection clustering described in the README.
    """
    defects = [e for e in EVENTS if e["event_type"] in ("pothole", "road_defect")]
    clusters: List[dict] = []

    for e in defects:
        placed = False
        for c in clusters:
            if _haversine_m(e["latitude"], e["longitude"], c["latitude"], c["longitude"]) <= radius_m:
                c["events"].append(e)
                placed = True
                break
        if not placed:
            clusters.append({"latitude": e["latitude"], "longitude": e["longitude"], "events": [e]})

    return [
        {
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "report_count": len(c["events"]),
            "max_severity": max(c["events"], key=lambda x: x["confidence"])["severity"],
            "event_ids": [x["event_id"] for x in c["events"]],
        }
        for c in clusters
        if len(c["events"]) >= min_reports
    ]


@app.get("/")
def root():
    return {"status": "ok", "events_stored": len(EVENTS)}
