"""
schemas/analytics.py
---------------------
Pydantic schemas for analytics endpoints.

All response shapes are designed to match the frontend mock data structures
in frontend/src/data/mockData.js exactly — so the frontend needs zero changes.
"""

from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Dict



# ── KPI Summary ──────────────────────────────────────────────────────────────

class KPIMetrics(BaseModel):
    """Response for GET /api/analytics/summary — powers the Overview KPI cards & integration callers."""
    activeBuses: int
    eventsToday: int
    potholesDetected: int
    trafficHotspots: int
    criticalAlerts: int

    # Integration stub / docs contract compatibility
    total_events: Optional[int] = None
    by_type: Optional[dict[str, int]] = None
    by_severity: Optional[dict[str, int]] = None



# ── Traffic Analytics ────────────────────────────────────────────────────────

class DensityPoint(BaseModel):
    time: str      # e.g. "06:00"
    density: float # average density score * 100 (percent)


class VehicleTypeCount(BaseModel):
    name: str      # "Cars", "Bikes", "Buses", "Trucks"
    value: int     # total count


class RouteStatus(BaseModel):
    id: str        # "Route 534"
    delay: str     # e.g. "14 min"
    density: str   # "HIGH" | "MEDIUM" | "LOW"


class TrafficAnalyticsResponse(BaseModel):
    """Response for GET /api/analytics/traffic."""
    densityOverTime: List[DensityPoint]
    vehicleTypes: List[VehicleTypeCount]
    routes: List[RouteStatus]


# ── Road Analytics ───────────────────────────────────────────────────────────

class SeverityCount(BaseModel):
    name: str      # "High Severity", "Medium Severity", "Low Severity"
    value: int


class DailyDefects(BaseModel):
    day: str       # "Mon", "Tue", ...
    newDefects: int
    resolved: int


class RoadAnalyticsResponse(BaseModel):
    """Response for GET /api/analytics/road."""
    severityDistribution: List[SeverityCount]
    defectsOverTime: List[DailyDefects]


# ── KPI Summaries for Analytics Pages ────────────────────────────────────────

class TrafficSummary(BaseModel):
    """KPI summary for TrafficAnalytics page."""
    totalVehicles: int
    avgTrafficDensity: int
    congestionHotspots: int
    criticalHotspots: int
    monitoringFleet: int
    activeCameras: int


class RoadSummary(BaseModel):
    """KPI summary for RoadAnalytics page."""
    totalPotholes: int
    highSeverityIssues: int
    persistentDefects: int
    resolvedDefects: int

