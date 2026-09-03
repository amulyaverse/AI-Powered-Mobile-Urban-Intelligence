"""
seed_rich.py
------------
Rich seed script for SIH 2026 Urban Intelligence Platform.

Generates:
  - 6 Transit Buses with realistic routes and status
  - 80 Road damage events (potholes, defects, congestion) clustered around 15 Delhi GPS locations
    (triggers automatic hotspot clustering and alert escalation)
  - 120 Vehicle count snapshots across 24h with realistic Delhi peak rush-hour curve
  - 8 System Alerts (critical, high, medium, low)

Usage:
  python backend/seed_rich.py
"""

from __future__ import annotations
import sys
import os
import random
from datetime import datetime, timezone, timedelta

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal, engine, Base
from app.models.bus import Bus
from app.models.event import Event
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.services.hotspot_service import process_event_for_hotspot

# Unsplash sample images for road defects and traffic
POTHOLE_IMAGES = [
    "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=600",
    "https://images.unsplash.com/photo-1578916171728-46686eac8d58?auto=format&fit=crop&q=80&w=600",
    "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=600",
]
CONGESTION_IMAGES = [
    "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=600",
    "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&q=80&w=600",
    "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?auto=format&fit=crop&q=80&w=600",
]

# 15 Delhi NCR GPS clusters (Lat, Lng, Location Name)
DELHI_CLUSTERS = [
    (28.5639, 77.2090, "AIIMS Ring Road Flyover"),
    (28.6239, 77.2290, "ITO Intersection"),
    (28.6139, 77.2090, "Connaught Place Outer Circle"),
    (28.5739, 77.2190, "Lajpat Nagar Central Market"),
    (28.6539, 77.2390, "Kashmere Gate ISBT"),
    (28.6339, 77.2490, "Delhi Gate / Asaf Ali Rd"),
    (28.5355, 77.2410, "Saket District Centre"),
    (28.5494, 77.2001, "IIT Flyover Outer Ring Rd"),
    (28.6289, 77.0818, "Janakpuri West Metro corridor"),
    (28.6989, 77.1389, "Pitampura Madhuban Chowk"),
    (28.5921, 77.2295, "Lodhi Road Junction"),
    (28.6448, 77.2167, "New Delhi Railway Station Paharganj"),
    (28.5245, 77.1855, "Mehrauli Badarpur Road"),
    (28.6712, 77.1214, "Punjabi Bagh Club Rd"),
    (28.5800, 77.0500, "Dwarka Sector 21 Expressway"),
]

BUS_FLEET = [
    {"id": "BUS_021", "route": "Route 534", "status": "Active", "camera": "Active", "lat": 28.5639, "lng": 77.2090, "traffic": "High"},
    {"id": "BUS_014", "route": "Route 419", "status": "Active", "camera": "Active", "lat": 28.6239, "lng": 77.2290, "traffic": "Medium"},
    {"id": "BUS_032", "route": "Route 720", "status": "Active", "camera": "Active", "lat": 28.6139, "lng": 77.2090, "traffic": "Low"},
    {"id": "BUS_045", "route": "Route 534", "status": "Active", "camera": "Active", "lat": 28.5739, "lng": 77.2190, "traffic": "High"},
    {"id": "BUS_017", "route": "Route 312", "status": "Maintenance", "camera": "Offline", "lat": 28.6539, "lng": 77.2390, "traffic": "Unknown"},
    {"id": "BUS_008", "route": "Route 419", "status": "Active", "camera": "Active", "lat": 28.6339, "lng": 77.2490, "traffic": "High"},
]


def seed():
    print("[Rich Seed] Initializing database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Clean slate
        print("[Clean] Clearing existing records...")
        db.query(SystemAlert).delete()
        db.query(Event).delete()
        db.query(Hotspot).delete()
        db.query(Bus).delete()
        db.commit()

        # 2. Insert Bus Fleet
        print(f"[Buses] Seeding {len(BUS_FLEET)} transit buses...")
        now = datetime.now(timezone.utc)
        for b in BUS_FLEET:
            bus = Bus(
                id=b["id"],
                route=b["route"],
                status=b["status"],
                camera_status=b["camera"],
                last_lat=b["lat"],
                last_lng=b["lng"],
                last_traffic=b["traffic"],
                last_seen=now - timedelta(minutes=random.randint(1, 15)),
            )
            db.add(bus)
        db.commit()

        # 3. Insert 80 Road Damage Events
        print("[Road] Seeding 80 Road Damage Events across Delhi clusters...")
        active_buses = [b["id"] for b in BUS_FLEET if b["status"] == "Active"]
        severities = ["high"] * 20 + ["medium"] * 35 + ["low"] * 25
        random.shuffle(severities)
        statuses = ["new"] * 30 + ["under_review"] * 20 + ["verified"] * 20 + ["resolved"] * 10
        random.shuffle(statuses)

        event_types = ["pothole"] * 40 + ["road_defect"] * 30 + ["congestion"] * 10
        random.shuffle(event_types)

        events_created = []

        for i in range(80):
            # Pick a cluster location: first 8 clusters repeat heavily to trigger hotspot intelligence
            if i < 48:
                cluster_idx = i % 8  # 6 occurrences each for first 8 clusters
                jitter_lat = random.uniform(-0.00015, 0.00015) # ~15 meters
                jitter_lng = random.uniform(-0.00015, 0.00015)
            else:
                cluster_idx = random.randint(8, len(DELHI_CLUSTERS) - 1)
                jitter_lat = random.uniform(-0.0003, 0.0003)
                jitter_lng = random.uniform(-0.0003, 0.0003)

            base_lat, base_lng, loc_name = DELHI_CLUSTERS[cluster_idx]
            lat = round(base_lat + jitter_lat, 6)
            lng = round(base_lng + jitter_lng, 6)

            etype = event_types[i]
            sev = severities[i]
            st = statuses[i]

            # Timestamp distributed over last 7 days
            days_ago = random.randint(0, 6)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            event_time = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            img = random.choice(POTHOLE_IMAGES if etype != "congestion" else CONGESTION_IMAGES)
            conf = round(random.uniform(0.78, 0.98), 2)
            bus_id = random.choice(active_buses)

            evt = Event(
                event_id=f"EVT_{i+1:03d}",
                event_type=etype,
                confidence=conf,
                severity=sev,
                bus_id=bus_id,
                camera_id="CAM_FRONT",
                latitude=lat,
                longitude=lng,
                timestamp=event_time,
                evidence=img,
                status=st,
                repeated_detections=1,
            )
            db.add(evt)
            db.flush()

            # Trigger hotspot intelligence
            process_event_for_hotspot(db, evt)
            events_created.append(evt)

        db.commit()
        print(f"   + {len(events_created)} road events inserted and clustered.")

        # 4. Insert 120 Traffic Snapshots (Rush Hour Curve)
        print("[Traffic] Seeding 120 Vehicle Count Snapshots (Rush-Hour Curve)...")
        traffic_events_count = 0

        # For each of the 6 buses, 20 hourly snapshots over past 24 hours
        for bus in BUS_FLEET:
            b_id = bus["id"]
            for h in range(20):
                hour_offset = 23 - h
                snap_time = now - timedelta(hours=hour_offset, minutes=random.randint(5, 50))
                hour_of_day = snap_time.hour

                # Realistic Delhi rush hour density curve
                if 0 <= hour_of_day < 6:
                    density = "LOW"
                    density_score = round(random.uniform(0.12, 0.28), 2)
                    cars = random.randint(5, 14)
                    bikes = random.randint(3, 8)
                    buses_c = random.randint(1, 2)
                    trucks = random.randint(0, 2)
                elif 6 <= hour_of_day < 11:
                    density = "HIGH"
                    density_score = round(random.uniform(0.70, 0.88), 2)
                    cars = random.randint(40, 65)
                    bikes = random.randint(25, 45)
                    buses_c = random.randint(4, 8)
                    trucks = random.randint(2, 5)
                elif 11 <= hour_of_day < 17:
                    density = "MEDIUM"
                    density_score = round(random.uniform(0.40, 0.65), 2)
                    cars = random.randint(20, 35)
                    bikes = random.randint(12, 22)
                    buses_c = random.randint(2, 5)
                    trucks = random.randint(1, 3)
                elif 17 <= hour_of_day < 21:
                    density = "CRITICAL"
                    density_score = round(random.uniform(0.85, 0.96), 2)
                    cars = random.randint(55, 80)
                    bikes = random.randint(35, 55)
                    buses_c = random.randint(5, 10)
                    trucks = random.randint(2, 5)
                else:
                    density = "MEDIUM"
                    density_score = round(random.uniform(0.30, 0.50), 2)
                    cars = random.randint(12, 28)
                    bikes = random.randint(8, 16)
                    buses_c = random.randint(1, 4)
                    trucks = random.randint(1, 2)

                total_v = cars + bikes + buses_c + trucks
                conf = round(random.uniform(0.85, 0.98), 2)

                traffic_evt = Event(
                    event_id=f"TRF_{b_id}_{h+1:02d}",
                    event_type="vehicle_count",
                    confidence=conf,
                    severity="low" if density == "LOW" else ("medium" if density == "MEDIUM" else "high"),
                    bus_id=b_id,
                    camera_id="CAM_FRONT",
                    latitude=round(bus["lat"] + random.uniform(-0.002, 0.002), 6),
                    longitude=round(bus["lng"] + random.uniform(-0.002, 0.002), 6),
                    timestamp=snap_time,
                    evidence=random.choice(CONGESTION_IMAGES),
                    status="verified",
                    repeated_detections=1,
                    car_count=cars,
                    bike_count=bikes,
                    bus_count=buses_c,
                    truck_count=trucks,
                    total_vehicles=total_v,
                    density=density,
                    density_score=density_score,
                )
                db.add(traffic_evt)
                traffic_events_count += 1

        db.commit()
        print(f"   + {traffic_events_count} traffic snapshots inserted.")

        # 5. Seed explicit system alerts to guarantee clear alert panel
        print("[Alerts] Checking and seeding System Alerts...")
        additional_alerts = [
            SystemAlert(
                id="ALT_001",
                severity="critical",
                message="Persistent severe pothole cluster detected on AIIMS Flyover",
                source="6 buses observed",
                details="Ring Road Flyover - Repeated high-impact hazard",
                timestamp=now - timedelta(minutes=4),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_002",
                severity="critical",
                message="Critical bottleneck gridlock at ITO Intersection",
                source="BUS_014 & BUS_021",
                details="Density Score 94% - Severe evening peak delay",
                timestamp=now - timedelta(minutes=15),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_003",
                severity="high",
                message="Deep trench defect expanding near Saket Metro",
                source="BUS_032",
                details="Saket District Centre - Verified by multiple passes",
                timestamp=now - timedelta(minutes=45),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_004",
                severity="high",
                message="Heavy road deterioration reported on Outer Ring Rd",
                source="BUS_045",
                details="IIT Delhi Flyover Ramp",
                timestamp=now - timedelta(hours=2),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_005",
                severity="medium",
                message="Surge in two-wheeler near-misses due to surface cracks",
                source="BUS_008",
                details="Delhi Gate Corridor",
                timestamp=now - timedelta(hours=3, minutes=20),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_006",
                severity="medium",
                message="Drainage grate displacement reported",
                source="BUS_014",
                details="ITO Vikas Marg feeder lane",
                timestamp=now - timedelta(hours=5),
                acknowledged=True,
            ),
            SystemAlert(
                id="ALT_007",
                severity="low",
                message="Camera lens glare obstruction reported on BUS_017",
                source="BUS_017",
                details="Front sensor flagged for scheduled depot maintenance",
                timestamp=now - timedelta(hours=14),
                acknowledged=False,
            ),
            SystemAlert(
                id="ALT_008",
                severity="low",
                message="Routine calibration update completed for Route 720",
                source="System",
                details="All 8 camera telemetry streams synchronised",
                timestamp=now - timedelta(hours=22),
                acknowledged=True,
            ),
        ]

        for alt in additional_alerts:
            db.merge(alt)

        db.commit()

        # Print summary
        hotspot_count = db.query(Hotspot).count()
        alert_count = db.query(SystemAlert).count()
        event_count = db.query(Event).count()
        bus_count = db.query(Bus).count()

        print("\n[Done] Rich Seed Completed Successfully!")
        print(f"   * Buses:         {bus_count}")
        print(f"   * Total Events:  {event_count} (80 road damage + {traffic_events_count} traffic snapshots)")
        print(f"   * Hotspots:      {hotspot_count} (organically generated via spatial clustering)")
        print(f"   * System Alerts: {alert_count}")


    finally:
        db.close()


if __name__ == "__main__":
    seed()
