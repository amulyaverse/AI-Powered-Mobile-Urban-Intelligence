"""
models/bus.py
-------------
ORM model for the Bus fleet table.
"""

from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Bus(Base):
    __tablename__ = "buses"

    id = Column(String(20), primary_key=True)       # e.g. "BUS_021"
    route = Column(String(50), nullable=True)        # e.g. "Route 534"
    status = Column(String(20), default="Active")    # Active | Maintenance | Offline
    camera_status = Column(String(20), default="Active")  # Active | Offline
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)
    last_traffic = Column(String(20), default="Unknown")  # Low | Medium | High | Unknown
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    events = relationship("Event", back_populates="bus", lazy="dynamic")
