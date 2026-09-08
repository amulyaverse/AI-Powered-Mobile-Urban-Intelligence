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
    Bus(id="BUS_01",  route="Route 102", status="Active",       camera_status="Active",  last_lat=28.6289, last_lng=77.2150, last_traffic="Medium",   last_seen=datetime.now(timezone.utc) - timedelta(minutes=1)),
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
        evidence="/evidence/pr37_snap_001.jpg",
        status="new", repeated_detections=6,
    ),
    Event(
        event_id="EVT_002", event_type="congestion", confidence=0.95, severity="high",
        bus_id="BUS_014", camera_id="CAM_FRONT", latitude=28.6239, longitude=77.2290,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
        evidence="/evidence/traffic_city.jpg",
        status="verified", repeated_detections=1,
    ),
    Event(
        event_id="EVT_003", event_type="road_defect", confidence=0.89, severity="medium",
        bus_id="BUS_032", camera_id="CAM_FRONT", latitude=28.6139, longitude=77.2090,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=9),
        evidence="/evidence/pr37_snap_003.jpg",
        status="under_review", repeated_detections=3,
    ),
    Event(
        event_id="EVT_004", event_type="pothole", confidence=0.78, severity="low",
        bus_id="BUS_045", camera_id="CAM_FRONT", latitude=28.5739, longitude=77.2190,
        timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
        evidence="/evidence/pr37_snap_005.jpg",
        status="new", repeated_detections=1,
    ),
    Event(
        event_id="EVT_005", event_type="congestion", confidence=0.88, severity="medium",
        bus_id="BUS_008", camera_id="CAM_FRONT", latitude=28.6339, longitude=77.2490,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
        evidence="/evidence/traffic_city.jpg",
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
                evidence="/evidence/traffic_city.jpg",
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


def seed_pr37_potholes(db: Session, max_events: int = 50) -> int:
    """
    Ingest pre-detected pothole telemetry from PR #37 (Pothole_Road_Condition_Model)
    jsonl dataset into the events table and trigger hotspot clustering.
    """
    import json
    from pathlib import Path
    import random
    from app.services.hotspot_service import process_event_for_hotspot

    # Ensure BUS_01 exists
    bus_01 = db.query(Bus).filter(Bus.id == "BUS_01").first()
    if not bus_01:
        bus_01 = Bus(
            id="BUS_01",
            route="Route 102",
            status="Active",
            camera_status="Active",
            last_lat=28.6289,
            last_lng=77.2150,
            last_traffic="Medium",
            last_seen=datetime.now(timezone.utc),
        )
        db.add(bus_01)
        db.flush()

    # Avoid duplicate seeding of PR 37 detections
    existing_pr37_count = db.query(Event).filter(Event.severity_method == "width_heuristic_pr37").count()
    if existing_pr37_count >= 20:
        return existing_pr37_count

    # Locate PR 37 jsonl file
    pr_root = Path(__file__).resolve().parents[2] / "edge-ai"
    jsonl_candidates = [
        pr_root / "pothole-latest" / "Pothole_Road_Condition_Model" / "pothole_events.jsonl",
        pr_root / "pothole-latest" / "Pothole_Road_Condition_Model" / "test_log.jsonl",
        pr_root / "Pothole_Road_Condition_Model" / "detected_events_approach_a-city_side.jsonl",
        pr_root / "Pothole_Road_Condition_Model" / "detected_events_approach_a.jsonl",
        pr_root / "pothole_Old" / "Pothole_Road_Condition_Model" / "detected_events_approach_a.jsonl",
    ]

    selected_file = None
    for cand in jsonl_candidates:
        if cand.exists():
            selected_file = cand
            break

    if not selected_file:
        print("[Seed] PR 37 jsonl file not found, skipping PR 37 event seed.")
        return 0

    print(f"[Seed] Ingesting PR 37 pothole telemetry from {selected_file.name}...")
    seeded = 0

    # Start coordinates in central Delhi corridor
    base_lat, base_lng = 28.6289, 77.2150

    with open(selected_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Sample events with high and medium confidence
    parsed_items = []
    for line in lines:
        try:
            item = json.loads(line)
            if item.get("confidence", 0.0) >= 0.50:
                parsed_items.append(item)
        except Exception:
            continue

    # Pick up to max_events evenly spaced
    step = max(1, len(parsed_items) // max_events) if parsed_items else 1
    selected_items = parsed_items[::step][:max_events]

    for idx, item in enumerate(selected_items):
        evt_id = f"EVT_PR37_{idx+1:03d}"
        if db.query(Event).filter(Event.event_id == evt_id).first():
            continue

        raw_sev_str = str(item.get("severity", "medium")).strip().lower().replace("-", "_").replace(" ", "_")
        if raw_sev_str in ("very_high", "veryhigh"):
            raw_sev = "critical"
        elif raw_sev_str in ("low", "medium", "high", "critical"):
            raw_sev = raw_sev_str
        else:
            raw_sev = "medium"
        conf = float(item.get("confidence", 0.75))

        # Synthetic GPS route step along corridor
        step_offset = (idx * 0.0012)
        evt_lat = round(base_lat + step_offset + random.uniform(-0.0003, 0.0003), 6)
        evt_lng = round(base_lng + (step_offset * 0.6) + random.uniform(-0.0003, 0.0003), 6)

        # Width and area ratios based on PR 37 Approach A heuristic
        if raw_sev in ("critical", "high"):
            w_ratio = round(random.uniform(0.24, 0.36), 3)
            a_ratio = round(random.uniform(0.062, 0.11), 4)
        elif raw_sev == "medium":
            w_ratio = round(random.uniform(0.10, 0.22), 3)
            a_ratio = round(random.uniform(0.016, 0.058), 4)
        else:
            w_ratio = round(random.uniform(0.04, 0.09), 3)
            a_ratio = round(random.uniform(0.005, 0.014), 4)

        # Bounding box in 640x480 frame
        box_w = int(w_ratio * 640)
        box_h = int(box_w * random.uniform(0.6, 0.9))
        x1 = random.randint(40, max(41, 600 - box_w))
        y1 = random.randint(180, max(181, 460 - box_h))
        x2 = min(639, x1 + box_w)
        y2 = min(479, y1 + box_h)
        bbox_json = json.dumps([x1, y1, x2, y2])

        # Parse timestamp
        raw_ts = item.get("timestamp")
        try:
            if isinstance(raw_ts, str) and " " in raw_ts:
                ts = datetime.fromisoformat(raw_ts.replace(" ", "T")).replace(tzinfo=None)
            else:
                ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=random.randint(2, 60))
        except Exception:
            ts = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=random.randint(2, 60))

        evt = Event(
            event_id=evt_id,
            event_type="pothole",
            confidence=conf,
            severity=raw_sev,
            bus_id="BUS_01",
            camera_id="CAM_FRONT",
            latitude=evt_lat,
            longitude=evt_lng,
            timestamp=ts,
            evidence=f"/evidence/pr37_snap_{((idx % 30) + 1):03d}.jpg",
            status="new" if raw_sev in ("critical", "high") else ("verified" if idx % 2 == 0 else "under_review"),
            repeated_detections=1,
            source_frame=idx * 15,
            frame_coverage_ratio=a_ratio,
            bbox=bbox_json,
            width_ratio=w_ratio,
            area_ratio=a_ratio,
            severity_method="width_heuristic_pr37",
            surface_condition="pothole",
        )
        db.add(evt)
        db.flush()
        process_event_for_hotspot(db, evt)
        seeded += 1

    db.commit()
    print(f"[Seed] Successfully seeded {seeded} PR 37 pothole events.")
    return seeded


def run_seed(db: Session) -> None:
    """
    Insert seed data if missing.
    Safe to call on every startup using merge() idempotence.
    """
    # 1. Seed fleet, sample events, and alerts using merge (never duplicates)
    for bus in SEED_BUSES:
        db.merge(bus)

    for event in SEED_EVENTS:
        db.merge(event)

    for alert in SEED_ALERTS:
        db.merge(alert)

    db.commit()
    print(f"[Seed] Fleet & alerts verified — {len(SEED_BUSES)} buses, {len(SEED_EVENTS)} events, {len(SEED_ALERTS)} alerts.")

    # 2. Ensure traffic telemetry exists for analytics charts
    seed_traffic_telemetry(db)

    # 3. Ensure PR 37 road defect telemetry exists for Road Analytics & GIS hotspots
    seed_pr37_potholes(db)

