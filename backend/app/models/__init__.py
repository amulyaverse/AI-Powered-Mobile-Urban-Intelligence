"""
models/__init__.py
------------------
Import all models here so Base.metadata.create_all() can discover them.
"""

from app.models.bus import Bus
from app.models.event import Event
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.models.ws_session import WsSession

__all__ = ["Bus", "Event", "Hotspot", "SystemAlert", "WsSession"]
