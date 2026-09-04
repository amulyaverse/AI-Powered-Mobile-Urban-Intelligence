"""
seed.py
-------
Seed the database with the initial bus fleet and a small set of sample events.

Run once on first startup (called automatically by main.py via create_tables).
Safe to run multiple times — uses INSERT OR IGNORE pattern via merge().
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.bus import Bus
from app.models.event import Event
from app.models.alert import SystemAlert


# ── Initial fleet ────────────────────────────────────────────────────────────

SEED_BUSES = [
    Bus(id="BUS_021", route="Route 534", status="Active",       camera_status="Active",  last_lat=28.5639, last_lng=77.2090, last_traffic="High",    last_seen=datetime.now(timezone.utc) - timedelta(minutes=2)),
    Bus(id="BUS_014", route="Route 419", status="Active",       camera_status="Active",  last_lat=28.6239, last_lng=77.2290, last_traffic="Medium",   last_seen=datetime.now(timezone.utc) - timedelta(minutes=5)),
    Bus(id="BUS_032", route="Route 720", status="Active",       camera_status="Active",  last_lat=28.6139, last_lng=77.2090, last_traffic="Low",      last_seen=datetime.now(timezone.utc) - timedelta(minutes=1)),
    Bus(id="BUS_045", route="Route 534", status="Active",       camera_status="Active",  last_lat=28.5739, last_lng=77.2190, last_traffic="High",     last_seen=datetime.now(timezone.utc) - timedelta(minutes=8)),
    Bus(id="BUS_017", route="Route 312", status="Maintenance",  camera_status="Offline", last_lat=28.6539, last_lng=77.2390, last_traffic="Unknown",  last_seen=datetime.now(timezone.utc) - timedelta(hours=24)),
    Bus(id="BUS_008", route="Route 419", status="Active",       camera_status="Active",  last_lat=28.6339, last_lng=77.2490, last_traffic="High",     last_seen=datetime.now(timezone.utc) - timedelta(minutes=2)),
]


# ── Sample events (mirrors the frontend mock data) ───────────────────────────

SEED_EVENTS = [
    Event(
        event_id="EVT_001", event_type="pothole", confidence=0.92, severity="high",
        bus_id="BUS_021", camera_id="CAM_FRONT", latitude=28.5639, longitude=77.2090,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=2),
        evidence="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
        status="new", repeated_detections=6,
    ),
    Event(
        event_id="EVT_002", event_type="congestion", confidence=0.95, severity="high",
        bus_id="BUS_014", camera_id="CAM_FRONT", latitude=28.6239, longitude=77.2290,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
        evidence="https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=400",
        status="verified", repeated_detections=1,
    ),
    Event(
        event_id="EVT_003", event_type="road_defect", confidence=0.89, severity="medium",
        bus_id="BUS_032", camera_id="CAM_FRONT", latitude=28.6139, longitude=77.2090,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=9),
        evidence="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
        status="under_review", repeated_detections=3,
    ),
    Event(
        event_id="EVT_004", event_type="pothole", confidence=0.78, severity="low",
        bus_id="BUS_045", camera_id="CAM_FRONT", latitude=28.5739, longitude=77.2190,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
        evidence="https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
        status="new", repeated_detections=1,
    ),
    Event(
        event_id="EVT_005", event_type="congestion", confidence=0.88, severity="medium",
        bus_id="BUS_008", camera_id="CAM_FRONT", latitude=28.6339, longitude=77.2490,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        evidence="https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=400",
        status="resolved", repeated_detections=2,
    ),
]


# ── Sample alerts ─────────────────────────────────────────────────────────────

SEED_ALERTS = [
    SystemAlert(
        id="ALT_001", severity="critical",
        message="High congestion detected",
        source="BUS_021", details="Ring Road intersection",
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=2),
    ),
    SystemAlert(
        id="ALT_002", severity="high",
        message="Persistent pothole detected",
        source="6 buses observed", details="Multiple verifications",
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=8),
    ),
    SystemAlert(
        id="ALT_003", severity="medium",
        message="New road defect detected",
        source="BUS_017", details="Sector 14 Main Road",
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=12),
    ),
]


def run_seed(db: Session) -> None:
    """
    Insert seed data only if the tables are empty.
    Safe to call on every startup.
    """
    # Only seed if buses table is empty
    if db.query(Bus).count() > 0:
        return

    print("[Seed] Seeding initial fleet and sample data...")

    for bus in SEED_BUSES:
        db.merge(bus)  # INSERT OR UPDATE

    for event in SEED_EVENTS:
        db.merge(event)

    for alert in SEED_ALERTS:
        db.merge(alert)

    db.commit()
    print(f"[Seed] Done — {len(SEED_BUSES)} buses, {len(SEED_EVENTS)} events, {len(SEED_ALERTS)} alerts seeded.")
