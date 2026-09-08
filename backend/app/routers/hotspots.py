"""
routers/hotspots.py
-------------------
Hotspot and system alert endpoints.

GET /api/hotspots   — persistent detection hotspots
GET /api/alerts     — system alerts for the Overview dashboard
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from datetime import datetime
from app.database import get_db
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.models.event import Event
from app.schemas.hotspot import HotspotResponse
from app.schemas.alert import SystemAlertResponse

router = APIRouter(tags=["Hotspots & Alerts"])


@router.get("/api/hotspots", response_model=List[HotspotResponse])
def list_hotspots(
    status: Optional[str] = Query(default="active", description="active | resolved | all"),
    min_reports: int = Query(default=1, description="Filter hotspots with at least this many reports"),
    radius_m: Optional[float] = Query(default=None, description="Stub compatibility parameter"),
    db: Session = Depends(get_db),
):
    """
    Return persistent detection hotspots.
    Ordered by priority_score descending — highest-priority issues first.
    Includes both GIS map properties and integration contract properties
    (latitude, longitude, report_count, max_severity, event_ids).
    """
    q = db.query(Hotspot)
    if status and status != "all":
        q = q.filter(Hotspot.status == status)
    if min_reports > 1:
        q = q.filter(Hotspot.detection_count >= min_reports)

    hotspots = q.order_by(Hotspot.priority_score.desc()).all()
    results = []
    for h in hotspots:
        event_ids = [e.event_id for e in h.events] if h.events else []
        results.append(
            HotspotResponse(
                id=h.id,
                center_lat=h.center_lat,
                center_lng=h.center_lng,
                event_type=h.event_type,
                detection_count=h.detection_count,
                severity=h.severity,
                priority_score=h.priority_score,
                first_seen=h.first_seen,
                last_seen=h.last_seen,
                status=h.status,
                event_ids=event_ids,
            )
        )
    return results


@router.get("/api/alerts", response_model=List[SystemAlertResponse])
def list_alerts(
    acknowledged: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """
    Return system alerts for the Overview AlertPanel.
    Combines explicit SystemAlert records and real high/critical Event incidents.
    Sorted newest-first.
    """
    results: List[SystemAlertResponse] = []
    seen_ids = set()

    # 1. Query manual SystemAlert rows
    q_alerts = db.query(SystemAlert)
    if acknowledged is not None:
        q_alerts = q_alerts.filter(SystemAlert.acknowledged == acknowledged)
    for a in q_alerts.order_by(func.datetime(SystemAlert.timestamp).desc()).limit(limit).all():
        results.append(
            SystemAlertResponse(
                id=a.id,
                severity=a.severity,
                message=a.message,
                source=a.source,
                details=a.details,
                timestamp=a.timestamp,
                acknowledged=a.acknowledged,
            )
        )
        seen_ids.add(a.id)

    # 2. Query high/critical real events from the Events table
    q_events = db.query(Event).filter(
        func.lower(Event.severity).in_(["critical", "high", "very high"])
    )
    if acknowledged is not None:
        if acknowledged:
            q_events = q_events.filter(Event.status.in_(["verified", "resolved"]))
        else:
            q_events = q_events.filter(Event.status.in_(["new", "under_review"]))

    real_events = q_events.order_by(func.datetime(Event.timestamp).desc()).limit(limit).all()
    for e in real_events:
        alert_id = f"ALT_{e.event_id}"
        if alert_id in seen_ids:
            continue
        seen_ids.add(alert_id)

        sev = "critical" if str(e.severity).lower() in ("critical", "very high") else "high"

        if e.event_type == "pothole":
            msg = f"Severe Pothole Detected - {e.event_id}"
        elif e.event_type == "road_defect":
            msg = f"Road Defect Detected - {e.event_id}"
        elif e.event_type == "congestion":
            msg = f"Traffic Congestion Alert - {e.event_id}"
        elif e.event_type == "vehicle_count":
            msg = f"Heavy Traffic Spike ({e.total_vehicles or 0} veh) - {e.event_id}"
        else:
            msg = f"{e.event_type.replace('_', ' ').title()} Alert - {e.event_id}"

        src = f"Bus {e.bus_id}" if e.bus_id else "AI Edge Node"
        det = f"Lat: {e.latitude:.4f}, Lng: {e.longitude:.4f} * Detections: {e.repeated_detections or 1} * Status: {e.status.replace('_', ' ').title()}"
        is_ack = e.status in ("verified", "resolved")

        results.append(
            SystemAlertResponse(
                id=alert_id,
                severity=sev,
                message=msg,
                source=src,
                details=det,
                timestamp=e.timestamp,
                acknowledged=is_ack,
            )
        )

    # Sort combined results descending by timestamp
    def get_sort_key(item):
        ts = item.timestamp
        if ts is not None and getattr(ts, "tzinfo", None):
            return ts.replace(tzinfo=None)
        return ts or datetime.min

    results.sort(key=get_sort_key, reverse=True)
    return results[:limit]


@router.patch("/api/alerts/{alert_id}/acknowledge", response_model=SystemAlertResponse)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """
    Mark a system alert as acknowledged.
    Supports both manual SystemAlert records and synthesized Event alerts.
    """
    # Check if this corresponds to a synthesized event alert
    if alert_id.startswith("ALT_"):
        target_event_id = alert_id[4:]
        event = db.query(Event).filter(Event.event_id == target_event_id).first()
        if event:
            event.status = "verified"
            db.commit()
            db.refresh(event)

            sev = "critical" if str(event.severity).lower() in ("critical", "very high") else "high"
            if event.event_type == "pothole":
                msg = f"Severe Pothole Detected - {event.event_id}"
            elif event.event_type == "road_defect":
                msg = f"Road Defect Detected - {event.event_id}"
            elif event.event_type == "congestion":
                msg = f"Traffic Congestion Alert - {event.event_id}"
            elif event.event_type == "vehicle_count":
                msg = f"Heavy Traffic Spike ({event.total_vehicles or 0} veh) - {event.event_id}"
            else:
                msg = f"{event.event_type.replace('_', ' ').title()} Alert - {event.event_id}"

            return SystemAlertResponse(
                id=alert_id,
                severity=sev,
                message=msg,
                source=f"Bus {event.bus_id}" if event.bus_id else "AI Edge Node",
                details=f"Lat: {event.latitude:.4f}, Lng: {event.longitude:.4f} * Detections: {event.repeated_detections or 1} * Status: {event.status.replace('_', ' ').title()}",
                timestamp=event.timestamp,
                acknowledged=True,
            )

    # Otherwise query SystemAlert
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert

