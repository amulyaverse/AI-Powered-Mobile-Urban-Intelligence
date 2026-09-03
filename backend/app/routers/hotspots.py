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

from app.database import get_db
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.schemas.hotspot import HotspotResponse
from app.schemas.alert import SystemAlertResponse

router = APIRouter(tags=["Hotspots & Alerts"])


@router.get("/api/hotspots", response_model=List[HotspotResponse])
def list_hotspots(
    status: Optional[str] = Query(default="active", description="active | resolved | all"),
    db: Session = Depends(get_db),
):
    """
    Return persistent detection hotspots.
    Ordered by priority_score descending — highest-priority issues first.
    """
    q = db.query(Hotspot)
    if status and status != "all":
        q = q.filter(Hotspot.status == status)
    return q.order_by(Hotspot.priority_score.desc()).all()


@router.get("/api/alerts", response_model=List[SystemAlertResponse])
def list_alerts(
    acknowledged: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """
    Return system alerts for the Overview AlertPanel.
    Sorted newest-first.
    """
    q = db.query(SystemAlert)
    if acknowledged is not None:
        q = q.filter(SystemAlert.acknowledged == acknowledged)
    return q.order_by(SystemAlert.timestamp.desc()).limit(limit).all()


@router.patch("/api/alerts/{alert_id}/acknowledge", response_model=SystemAlertResponse)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """
    Mark a system alert as acknowledged.
    """
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert

