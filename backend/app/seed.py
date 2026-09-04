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


def seed_traffic_telemetry(db: Session) -> None:
    """
    Seed 24-hour vehicle count snapshots across active bus routes
    if none exist, ensuring Traffic Analytics charts always have rich data.
    """
    import random
    if db.query(Event).filter(Event.event_type == "vehicle_count").count() > 0:
        return

    print("[Seed] Seeding 24-hour traffic telemetry snapshots...")
    now = datetime.now(timezone.utc)
    buses = db.query(Bus).filter(Bus.status == "Active").all()
    if not buses:
        buses = SEED_BUSES[:4]

    for b in buses:
        for h in range(24):
            snap_time = now - timedelta(hours=23 - h, minutes=random.randint(5, 50))
            hour = snap_time.hour

            if 7 <= hour <= 10:
                density, score = "HIGH", round(random.uniform(0.72, 0.88), 2)
                cars, bikes, bc, trucks = random.randint(45, 70), random.randint(25, 45), random.randint(4, 8), random.randint(2, 5)
            elif 17 <= hour <= 21:
                density, score = "CRITICAL", round(random.uniform(0.85, 0.95), 2)
                cars, bikes, bc, trucks = random.randint(55, 80), random.randint(35, 55), random.randint(5, 10), random.randint(2, 5)
            elif 11 <= hour <= 16:
                density, score = "MEDIUM", round(random.uniform(0.40, 0.65), 2)
                cars, bikes, bc, trucks = random.randint(25, 40), random.randint(15, 25), random.randint(2, 5), random.randint(1, 3)
            else:
                density, score = "LOW", round(random.uniform(0.15, 0.30), 2)
                cars, bikes, bc, trucks = random.randint(8, 18), random.randint(4, 10), random.randint(1, 2), random.randint(0, 2)

            total_v = cars + bikes + bc + trucks
            evt = Event(
                event_id=f"TRF_{b.id}_{h:02d}",
                event_type="vehicle_count",
                confidence=round(random.uniform(0.88, 0.98), 2),
                severity="low" if density == "LOW" else ("medium" if density == "MEDIUM" else "high"),
                bus_id=b.id,
                camera_id="CAM_FRONT",
                latitude=round((b.last_lat or 28.6139) + random.uniform(-0.002, 0.002), 6),
                longitude=round((b.last_lng or 77.2090) + random.uniform(-0.002, 0.002), 6),
                timestamp=snap_time,
                evidence="https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=400",
                status="verified",
                repeated_detections=1,
                car_count=cars,
                bike_count=bikes,
                bus_count=bc,
                truck_count=trucks,
                total_vehicles=total_v,
                density=density,
                density_score=score,
            )
            db.merge(evt)

    db.commit()
    print("[Seed] Traffic telemetry snapshots seeded successfully.")


def run_seed(db: Session) -> None:
    """
    Insert seed data only if the tables are empty.
    Safe to call on every startup.
    """
    # 1. Seed fleet and sample events if buses table is empty
    if db.query(Bus).count() == 0:
        print("[Seed] Seeding initial fleet and sample data...")
        for bus in SEED_BUSES:
            db.merge(bus)

        for event in SEED_EVENTS:
            db.merge(event)

        for alert in SEED_ALERTS:
            db.merge(alert)

        db.commit()
        print(f"[Seed] Done — {len(SEED_BUSES)} buses, {len(SEED_EVENTS)} events, {len(SEED_ALERTS)} alerts seeded.")

    # 2. Ensure traffic telemetry exists for analytics charts
    seed_traffic_telemetry(db)

