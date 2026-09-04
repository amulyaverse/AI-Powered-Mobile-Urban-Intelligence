"""
models/hotspot.py
-----------------
ORM model for the Hotspot table.

A hotspot is a geographic cluster of events at roughly the same location,
detected by multiple buses. This is the "persistent detection intelligence layer".
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    center_lat = Column(Float, nullable=False)         # Centroid latitude of cluster
    center_lng = Column(Float, nullable=False)         # Centroid longitude of cluster
    event_type = Column(String(30), nullable=False)    # Dominant type in the cluster
    detection_count = Column(Integer, default=1)       # How many buses reported this location
    severity = Column(String(20), default="low")       # Escalates with detection_count
    priority_score = Column(Float, default=0.0)        # count × avg_confidence × severity_weight
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="active")      # active | resolved

    # Relationships
    events = relationship("Event", back_populates="hotspot", lazy="dynamic")
