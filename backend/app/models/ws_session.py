"""
models/ws_session.py
---------------------
ORM model for the ws_sessions table.

Each row represents one edge-device camera connection to
WS /api/ws/camera/{bus_id}.  The table gives operators an audit trail:
  - Which bus cameras connected and when
  - How many frames were received / actually inferred
  - How many events were generated per session
  - When the session ended (or None if still active)
"""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone

from app.database import Base


class WsSession(Base):
    __tablename__ = "ws_sessions"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    bus_id          = Column(String(20), nullable=False,   index=True)
    mode            = Column(String(20), default="traffic")  # traffic | pothole
    connected_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    disconnected_at = Column(DateTime, nullable=True)
    frames_received = Column(Integer, default=0)  # total frames sent by edge device
    frames_inferred = Column(Integer, default=0)  # frames that actually ran YOLO
    events_emitted  = Column(Integer, default=0)  # events that passed aggregation & were stored
