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
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_DB_PATH = BACKEND_DIR / "urban_intelligence.db"
DEFAULT_EVIDENCE_DIR = PROJECT_ROOT / "frontend" / "public" / "evidence"


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    # Managed cloud DB (Supabase / Railway / Neon) or local PostgreSQL.
    # Example: postgresql://user:password@host:5432/dbname
    # Fallback: SQLite in backend directory for local testing without a cloud DB.
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    EVIDENCE_DIR: Path = DEFAULT_EVIDENCE_DIR


    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI-Powered Mobile Urban Intelligence API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    AUTO_SEED: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Add your Vercel frontend URL here for production.
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,https://ai-powered-mobile-urban-intelligenc.vercel.app"

    # ── Hotspot Logic ─────────────────────────────────────────────────────────
    # Radius (metres) within which events are considered the same hotspot.
    HOTSPOT_RADIUS_METRES: float = 50.0
    # Number of detections that trigger a system alert and severity escalation.
    HOTSPOT_ALERT_THRESHOLD: int = 3

    # ── Confidence ────────────────────────────────────────────────────────────
    # Events below this confidence are rejected at ingestion time.
    MIN_CONFIDENCE: float = 0.65

    # ── WebSocket Camera Streaming ────────────────────────────────────────────
    # Inference runs at 2 fps (every 500 ms). Frames arriving faster are
    # received and acknowledged but skipped for YOLO processing.
    WS_FRAME_SAMPLE_INTERVAL_SEC: float = 0.5
    # Hard cap per incoming frame — reject frames larger than this.
    WS_MAX_FRAME_SIZE_BYTES: int = 512_000  # 500 KB

    # ── YOLO Inference ────────────────────────────────────────────────────────
    # Model weights: a hub model name (e.g. "yolov8n.pt") or an absolute path
    # to custom-trained weights (e.g. edge-ai/pothole/best.pt).
    YOLO_POTHOLE_WEIGHTS: str = "yolov8n.pt"
    YOLO_TRAFFIC_WEIGHTS: str = "yolov8n.pt"
    INFERENCE_CONFIDENCE: float = 0.25      # YOLO detection confidence threshold
    INFERENCE_IOU: float = 0.45             # NMS IoU threshold

    # ── Event Aggregation / Deduplication ────────────────────────────────────
    # Suppress repeated events of the same type from the same bus within
    # this window (seconds) to avoid DB flooding from continuous 2-fps streams.
    AGGREGATOR_SUPPRESS_WINDOW_SEC: float = 2.0
    # Override suppression if the new detection's confidence exceeds the
    # cached one by at least this delta (emit a better detection anyway).
    AGGREGATOR_CONF_OVERRIDE_DELTA: float = 0.15

    # ── Live Bus Startup & Location Vicinity ─────────────────────────────────
    # Target bus randomized in Delhi on server startup and vicinity bounds.
    TARGET_BUS_ID: str = "BUS_021"
    BUS_VICINITY_RADIUS_KM: float = 3.0

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — reads .env once at startup."""
    return Settings()
