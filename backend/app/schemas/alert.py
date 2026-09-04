"""
schemas/alert.py
----------------
Pydantic schemas for SystemAlert endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemAlertResponse(BaseModel):
    id: str
    severity: str
    message: str
    source: Optional[str]
    details: Optional[str]
    timestamp: datetime
    acknowledged: bool

    model_config = {"from_attributes": True}
