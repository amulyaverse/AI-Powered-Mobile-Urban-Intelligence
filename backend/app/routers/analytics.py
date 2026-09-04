"""
routers/analytics.py
---------------------
Analytics endpoints powering the dashboard charts and KPI cards.

GET /api/analytics/summary  — KPI cards on Overview
GET /api/analytics/traffic  — TrafficAnalytics page charts
GET /api/analytics/road     — RoadAnalytics page charts
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.event import Event
from app.models.bus import Bus
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.schemas.analytics import (
    KPIMetrics,
    TrafficAnalyticsResponse,
    RoadAnalyticsResponse,
    DensityPoint,
    VehicleTypeCount,
    RouteStatus,
    SeverityCount,
    DailyDefects,
    TrafficSummary,
    RoadSummary,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=KPIMetrics)
def get_summary(db: Session = Depends(get_db)):
    """
    Return KPI metrics for the Overview dashboard cards.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    active_buses = db.query(func.count(Bus.id)).filter(Bus.status == "Active").scalar() or 0

    events_today = (
        db.query(func.count(Event.event_id))
        .filter(Event.timestamp >= today_start)
        .scalar() or 0
    )

    potholes_detected = (
        db.query(func.count(Event.event_id))
        .filter(Event.event_type == "pothole")
        .filter(Event.timestamp >= today_start)
        .scalar() or 0
    )

    traffic_hotspots = (
        db.query(func.count(Hotspot.id))
        .filter(Hotspot.status == "active")
        .scalar() or 0
    )

    critical_alerts = (
        db.query(func.count(SystemAlert.id))
        .filter(SystemAlert.severity == "critical")
        .filter(SystemAlert.acknowledged == False)
        .scalar() or 0
    )

    return KPIMetrics(
        activeBuses=active_buses,
        eventsToday=events_today,
        potholesDetected=potholes_detected,
        trafficHotspots=traffic_hotspots,
        criticalAlerts=critical_alerts,
    )


@router.get("/traffic", response_model=TrafficAnalyticsResponse)
def get_traffic_analytics(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """
    Return traffic analytics for the TrafficAnalytics page.

    - densityOverTime: average density score per 2-hour bucket
    - vehicleTypes: total counts per vehicle class
    - routes: aggregated congestion per bus route
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    traffic_events = (
        db.query(Event)
        .filter(Event.event_type == "vehicle_count")
        .filter(Event.timestamp >= since)
        .order_by(Event.timestamp)
        .all()
    )

    # ── Density over time (2-hour buckets) ────────────────────────────────────
    bucket_scores: dict[str, list[float]] = defaultdict(list)
    for e in traffic_events:
        # Round to nearest 2-hour slot
        hour = (e.timestamp.hour // 2) * 2
        label = f"{hour:02d}:00"
        if e.density_score is not None:
            bucket_scores[label].append(e.density_score * 100)

    density_over_time = [
        DensityPoint(time=t, density=round(sum(v) / len(v), 1))
        for t, v in sorted(bucket_scores.items())
    ] or [DensityPoint(time="No data", density=0)]

    # ── Vehicle type totals ───────────────────────────────────────────────────
    car_total   = sum(e.car_count or 0 for e in traffic_events)
    bike_total  = sum(e.bike_count or 0 for e in traffic_events)
    bus_total   = sum(e.bus_count or 0 for e in traffic_events)
    truck_total = sum(e.truck_count or 0 for e in traffic_events)

    vehicle_types = [
        VehicleTypeCount(name="Cars",   value=car_total),
        VehicleTypeCount(name="Bikes",  value=bike_total),
        VehicleTypeCount(name="Buses",  value=bus_total),
        VehicleTypeCount(name="Trucks", value=truck_total),
    ]

    # ── Route congestion (group by bus route) ────────────────────────────────
    # Join with Bus table to get route information
    route_stats: dict[str, list[str]] = defaultdict(list)
    for e in traffic_events:
        bus = db.query(Bus).filter(Bus.id == e.bus_id).first()
        if bus and bus.route and e.density:
            route_stats[bus.route].append(e.density)

    routes = []
    density_to_delay = {"LOW": "2 min", "MEDIUM": "8 min", "HIGH": "14 min", "CRITICAL": "20+ min"}
    for route_name, densities in route_stats.items():
        # Most common density label for this route
        dominant = max(set(densities), key=densities.count) if densities else "LOW"
        routes.append(RouteStatus(
            id=route_name,
            delay=density_to_delay.get(dominant, "5 min"),
            density=dominant,
        ))

    return TrafficAnalyticsResponse(
        densityOverTime=density_over_time,
        vehicleTypes=vehicle_types,
        routes=routes,
    )


@router.get("/road", response_model=RoadAnalyticsResponse)
def get_road_analytics(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """
    Return road condition analytics for the RoadAnalytics page.

    - severityDistribution: counts of high/medium/low severity defects
    - defectsOverTime: daily new detections vs resolved for the last N days
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    road_types = ("pothole", "road_defect")

    # ── Severity distribution ─────────────────────────────────────────────────
    high   = db.query(func.count(Event.event_id)).filter(Event.event_type.in_(road_types), Event.severity == "high").scalar() or 0
    medium = db.query(func.count(Event.event_id)).filter(Event.event_type.in_(road_types), Event.severity == "medium").scalar() or 0
    low    = db.query(func.count(Event.event_id)).filter(Event.event_type.in_(road_types), Event.severity == "low").scalar() or 0

    severity_distribution = [
        SeverityCount(name="High Severity",   value=high),
        SeverityCount(name="Medium Severity", value=medium),
        SeverityCount(name="Low Severity",    value=low),
    ]

    # ── Defects over time (last N days) ──────────────────────────────────────
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    defects_over_time = []

    for i in range(days - 1, -1, -1):
        day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end   = day_start + timedelta(days=1)
        day_label = day_names[day_start.weekday()]

        new_count = (
            db.query(func.count(Event.event_id))
            .filter(Event.event_type.in_(road_types))
            .filter(Event.timestamp >= day_start, Event.timestamp < day_end)
            .scalar() or 0
        )
        resolved_count = (
            db.query(func.count(Event.event_id))
            .filter(Event.event_type.in_(road_types))
            .filter(Event.status == "resolved")
            .filter(Event.timestamp >= day_start, Event.timestamp < day_end)
            .scalar() or 0
        )
        defects_over_time.append(DailyDefects(
            day=day_label,
            newDefects=new_count,
            resolved=resolved_count,
        ))

    return RoadAnalyticsResponse(
        severityDistribution=severity_distribution,
        defectsOverTime=defects_over_time,
    )


@router.get("/traffic/summary", response_model=TrafficSummary)
def get_traffic_summary(db: Session = Depends(get_db)):
    """
    Return top KPI summary metrics for the TrafficAnalytics page.
    """
    traffic_events = (
        db.query(Event)
        .filter(Event.event_type == "vehicle_count")
        .all()
    )

    total_vehicles = sum(
        (e.total_vehicles if e.total_vehicles is not None else (
            (e.car_count or 0) + (e.bike_count or 0) + (e.bus_count or 0) + (e.truck_count or 0)
        ))
        for e in traffic_events
    )

    density_scores = [e.density_score for e in traffic_events if e.density_score is not None]
    avg_density = round((sum(density_scores) / len(density_scores)) * 100) if density_scores else 0

    congestion_hotspots = (
        db.query(func.count(Hotspot.id))
        .filter(Hotspot.status == "active")
        .scalar() or 0
    )

    critical_hotspots = (
        db.query(func.count(Hotspot.id))
        .filter(Hotspot.status == "active", Hotspot.severity.in_(["high", "critical"]))
        .scalar() or 0
    )

    monitoring_fleet = (
        db.query(func.count(Bus.id))
        .filter(Bus.status == "Active")
        .scalar() or 0
    )

    active_cameras = (
        db.query(func.count(Bus.id))
        .filter(Bus.camera_status == "Active")
        .scalar() or 0
    )

    return TrafficSummary(
        totalVehicles=total_vehicles,
        avgTrafficDensity=avg_density,
        congestionHotspots=congestion_hotspots,
        criticalHotspots=critical_hotspots,
        monitoringFleet=monitoring_fleet,
        activeCameras=active_cameras,
    )


@router.get("/road/summary", response_model=RoadSummary)
def get_road_summary(db: Session = Depends(get_db)):
    """
    Return top KPI summary metrics for the RoadAnalytics page.
    """
    road_types = ("pothole", "road_defect")

    total_potholes = (
        db.query(func.count(Event.event_id))
        .filter(Event.event_type == "pothole")
        .scalar() or 0
    )

    high_severity = (
        db.query(func.count(Event.event_id))
        .filter(Event.event_type.in_(road_types), Event.severity == "high")
        .scalar() or 0
    )

    persistent = (
        db.query(func.count(Hotspot.id))
        .filter(Hotspot.detection_count >= 3)
        .scalar() or 0
    )

    resolved = (
        db.query(func.count(Event.event_id))
        .filter(Event.event_type.in_(road_types), Event.status == "resolved")
        .scalar() or 0
    )

    return RoadSummary(
        totalPotholes=total_potholes,
        highSeverityIssues=high_severity,
        persistentDefects=persistent,
        resolvedDefects=resolved,
    )

