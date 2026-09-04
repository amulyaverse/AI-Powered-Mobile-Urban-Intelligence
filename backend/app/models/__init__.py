"""
models/__init__.py
------------------
Import all models here so Alembic's autogenerate can discover them.
"""

from app.models.bus import Bus
from app.models.event import Event
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert

__all__ = ["Bus", "Event", "Hotspot", "SystemAlert"]
