"""
services/bus_location_service.py
---------------------------------
Service for managing Delhi GPS coordinates and ensuring bus detection events
remain within the specified vicinity (3 kilometers) of the bus's location.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session

from app.models.bus import Bus
from app.models.event import Event
from app.models.hotspot import Hotspot


# ── 20 Realistic Delhi NCR Urban Transit Corridors & Landmarks ────────────────
DELHI_CLUSTERS: List[Tuple[float, float, str]] = [
    (28.5639, 77.2090, "AIIMS Ring Road Flyover"),
    (28.6315, 77.2167, "Connaught Place Outer Circle"),
    (28.6239, 77.2290, "ITO Intersection"),
    (28.6675, 77.2285, "Kashmere Gate ISBT"),
    (28.5284, 77.2192, "Saket District Centre"),
    (28.5700, 77.2370, "Lajpat Nagar Ring Road"),
    (28.5494, 77.2001, "IIT Flyover Outer Ring Rd"),
    (28.6289, 77.0818, "Janakpuri West Metro corridor"),
    (28.6989, 77.1389, "Pitampura Madhuban Chowk"),
    (28.6465, 77.1905, "Karol Bagh Pusa Road"),
    (28.5921, 77.2295, "Lodhi Road Junction"),
    (28.6448, 77.2167, "New Delhi Railway Station Paharganj"),
    (28.6712, 77.1214, "Punjabi Bagh Club Rd"),
    (28.5520, 77.0585, "Dwarka Sector 21 Expressway"),
    (28.6380, 77.2410, "Delhi Gate / Asaf Ali Rd"),
    (28.7150, 77.1190, "Rohini Sector 10"),
    (28.5490, 77.2530, "Nehru Place Commercial Hub"),
    (28.6080, 77.2940, "Mayur Vihar Phase 1"),
    (28.6810, 77.2230, "Civil Lines Ring Road"),
    (28.6560, 77.2320, "Chandni Chowk / Red Fort"),
]

# Delhi NCR Urban Bounding Box
DELHI_BOUNDS = {
    "min_lat": 28.4500,
    "max_lat": 28.7500,
    "min_lng": 77.0500,
    "max_lng": 77.3500,
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    R = 6371.0088  # Mean Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_random_delhi_coordinates() -> Tuple[float, float, str]:
    """
    Select a random Delhi location from the curated transit corridors
    with realistic street-level jitter (within ~200-400m of corridor hub).
    """
    base_lat, base_lng, loc_name = random.choice(DELHI_CLUSTERS)
    # Slight jitter around cluster (~200m)
    lat = round(base_lat + random.uniform(-0.002, 0.002), 6)
    lng = round(base_lng + random.uniform(-0.002, 0.002), 6)

    # Clamp to Delhi NCR bounds
    lat = max(DELHI_BOUNDS["min_lat"], min(DELHI_BOUNDS["max_lat"], lat))
    lng = max(DELHI_BOUNDS["min_lng"], min(DELHI_BOUNDS["max_lng"], lng))
    return lat, lng, loc_name


def get_vicinity_coordinates(
    base_lat: float,
    base_lng: float,
    max_radius_km: float = 3.0,
    step: int = 0,
) -> Tuple[float, float]:
    """
    Generate coordinates strictly within `max_radius_km` (default: 3.0 km) of `(base_lat, base_lng)`.

    Supports an optional `step` index for progressive stream frames or sequential events
    along a simulated transit route corridor.
    """
    # Keep radius strictly under max_radius_km (e.g. 0.05 km to 2.85 km)
    safe_max_km = max(0.1, max_radius_km * 0.95)

    if step > 0:
        # Structured progression along a route direction with slight meandering
        base_angle = 0.7854  # 45 degrees
        angle = base_angle + (step * 0.08)
        # Advance radius with cyclical wrapping within the 3km boundary
        dist_km = 0.15 + ((step * 0.04) % (safe_max_km - 0.2))
    else:
        # Uniform random distribution within circle
        dist_km = random.uniform(0.05, safe_max_km)
        angle = random.uniform(0.0, 2.0 * math.pi)

    # Convert km distance to degree offsets
    delta_lat = (dist_km * math.cos(angle)) / 111.32
    avg_lat = math.radians(base_lat)
    cos_lat = max(0.1, math.cos(avg_lat))
    delta_lng = (dist_km * math.sin(angle)) / (111.32 * cos_lat)

    new_lat = round(base_lat + delta_lat, 6)
    new_lng = round(base_lng + delta_lng, 6)

    # Double check with Haversine formula and guarantee boundary
    actual_dist = haversine_distance_km(base_lat, base_lng, new_lat, new_lng)
    if actual_dist > max_radius_km:
        scale = (safe_max_km / actual_dist)
        new_lat = round(base_lat + delta_lat * scale, 6)
        new_lng = round(base_lng + delta_lng * scale, 6)

    return new_lat, new_lng


def randomize_bus_on_startup(
    db: Session,
    bus_id: str,
    max_radius_km: float = 3.0,
) -> dict:
    """
    Randomize coordinates for `bus_id` in Delhi on backend server startup,
    and relocate all existing detections of that bus to within `max_radius_km` (3.0 km).
    """
    new_lat, new_lng, loc_name = get_random_delhi_coordinates()

    # 1. Update or create the target bus
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        bus = Bus(
            id=bus_id,
            route="Route 534",
            status="Active",
            camera_status="Active",
            last_traffic="Medium",
        )
        db.add(bus)

    bus.last_lat = new_lat
    bus.last_lng = new_lng
    bus.last_seen = datetime.now(timezone.utc)
    bus.status = "Active"
    db.flush()

    # 2. Update all detections for this bus to be in the 3 km vicinity
    events = db.query(Event).filter(Event.bus_id == bus_id).all()
    events_updated = len(events)
    for idx, event in enumerate(events):
        evt_lat, evt_lng = get_vicinity_coordinates(
            new_lat, new_lng, max_radius_km=max_radius_km, step=idx + 1
        )
        event.latitude = evt_lat
        event.longitude = evt_lng

    # 3. Recalculate centroids for any hotspots referencing these events
    if events_updated > 0:
        event_ids_set = {e.event_id for e in events}
        all_hotspots = db.query(Hotspot).all()
        for hs in all_hotspots:
            try:
                import json
                hs_evt_ids = json.loads(hs.event_ids) if isinstance(hs.event_ids, str) else []
            except Exception:
                hs_evt_ids = []
            
            matched = [eid for eid in hs_evt_ids if eid in event_ids_set]
            if matched:
                # Update hotspot centroid to vicinity
                hs_events = db.query(Event).filter(Event.event_id.in_(hs_evt_ids)).all()
                if hs_events:
                    hs.center_lat = round(sum(e.latitude for e in hs_events) / len(hs_events), 6)
                    hs.center_lng = round(sum(e.longitude for e in hs_events) / len(hs_events), 6)

    db.commit()
    db.refresh(bus)

    summary = {
        "bus_id": bus_id,
        "lat": new_lat,
        "lng": new_lng,
        "location": loc_name,
        "events_updated": events_updated,
        "vicinity_radius_km": max_radius_km,
    }
    print(
        f"[Startup] Bus {bus_id} randomly placed at {loc_name} ({new_lat}, {new_lng}). "
        f"{events_updated} detections placed within {max_radius_km} km."
    )
    return summary
