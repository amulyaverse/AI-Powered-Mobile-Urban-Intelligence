"""
schemas/__init__.py
"""
from app.schemas.event import EventCreate, EventResponse, EventStatusUpdate
from app.schemas.bus import BusResponse, BusLocationUpdate
from app.schemas.analytics import KPIMetrics, TrafficAnalyticsResponse, RoadAnalyticsResponse
from app.schemas.alert import SystemAlertResponse
from app.schemas.hotspot import HotspotResponse
