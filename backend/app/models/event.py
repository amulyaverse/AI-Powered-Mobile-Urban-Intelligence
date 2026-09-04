"""
models/event.py
---------------
ORM model for the core Events table.

Stores every AI detection — pothole, road_defect, congestion, vehicle_count.
Traffic snapshots (vehicle count events) also go here per the agreed schema.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String(40), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(30), nullable=False)   # pothole | road_defect | congestion | vehicle_count
    confidence = Column(Float, nullable=False)         # 0.0 – 1.0
    severity = Column(String(20), nullable=False)      # low | medium | high | critical
    bus_id = Column(String(20), ForeignKey("buses.id", ondelete="SET NULL"), nullable=True)
    camera_id = Column(String(30), nullable=True)      # CAM_FRONT | CAM_REAR
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)       # UTC timestamp of detection
    evidence = Column(Text, nullable=True)             # URL or placeholder
    status = Column(String(20), default="new")         # new | under_review | verified | resolved
    repeated_detections = Column(Integer, default=1)   # incremented by hotspot logic
    hotspot_id = Column(Integer, ForeignKey("hotspots.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Extra fields for vehicle_count events (traffic AI output)
    car_count = Column(Integer, nullable=True)
    bike_count = Column(Integer, nullable=True)
    bus_count = Column(Integer, nullable=True)
    truck_count = Column(Integer, nullable=True)
    total_vehicles = Column(Integer, nullable=True)
    density = Column(String(20), nullable=True)        # LOW | MEDIUM | HIGH | CRITICAL
    density_score = Column(Float, nullable=True)       # 0.0 – 1.0

    # Relationships
    bus = relationship("Bus", back_populates="events")
    hotspot = relationship("Hotspot", back_populates="events")
