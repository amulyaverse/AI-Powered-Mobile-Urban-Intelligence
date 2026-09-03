"""
config.py
---------
Centralised configuration via environment variables.
All settings can be overridden through a .env file in the backend/ directory.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "urban_intelligence.db"


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    # Managed cloud DB (Supabase / Railway / Neon) or local PostgreSQL.
    # Example: postgresql://user:password@host:5432/dbname
    # Fallback: SQLite in backend directory for local testing without a cloud DB.
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI-Powered Mobile Urban Intelligence API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Add your Vercel frontend URL here for production.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,https://ai-powered-mobile-urban-intelligenc.vercel.app"

    # ── Hotspot Logic ─────────────────────────────────────────────────────────
    # Radius (metres) within which events are considered the same hotspot.
    HOTSPOT_RADIUS_METRES: float = 50.0
    # Number of detections that trigger a system alert and severity escalation.
    HOTSPOT_ALERT_THRESHOLD: int = 3

    # ── Confidence ────────────────────────────────────────────────────────────
    # Events below this confidence are rejected at ingestion time.
    MIN_CONFIDENCE: float = 0.65

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — reads .env once at startup."""
    return Settings()
