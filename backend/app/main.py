"""
main.py
-------
FastAPI application entry point.

Startup sequence:
  1. Create all DB tables (Alembic handles migrations in production)
  2. Run seed script to populate initial fleet if tables are empty
  3. Register all API routers
  4. Add CORS middleware for frontend dev server

Run locally:
  cd backend
  uvicorn app.main:app --reload --port 8000

Visit the interactive API docs at: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings
from app.database import engine, Base, SessionLocal, get_db, migrate_db
from app.models import Bus, Event, Hotspot, SystemAlert, WsSession  # noqa — ensure models are registered
from app.seed import run_seed
from app.routers import events, buses, analytics, hotspots, videos
from app.routers import camera_ws, events_ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables, run migrations, seed data, and randomize bus coordinates on startup."""
    Base.metadata.create_all(bind=engine)
    migrate_db(engine)
    db = SessionLocal()
    try:
        if settings.AUTO_SEED:
            run_seed(db)
        # Randomize target bus coordinates somewhere in Delhi whenever server goes live,
        # and ensure all detections of that bus are in the 3 km vicinity.
        from app.services.bus_location_service import randomize_bus_on_startup
        randomize_bus_on_startup(db, settings.TARGET_BUS_ID, settings.BUS_VICINITY_RADIUS_KM)
    finally:
        db.close()
    yield  # App is running
    # Cleanup (if any) goes here


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend API for the AI-Powered Mobile Urban Intelligence Platform (SIH'26). "
        "Ingests traffic and road-condition events from edge-AI bus cameras and serves "
        "the GIS dashboard with real-time analytics."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Evidence Assets ──────────────────────────────────────────────────
settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/evidence", StaticFiles(directory=str(settings.EVIDENCE_DIR)), name="evidence")

# ── Routers ─────────────────────────────────────────────────────────────────────
app.include_router(events.router)
app.include_router(buses.router)
app.include_router(analytics.router)
app.include_router(hotspots.router)
app.include_router(videos.router)

# ── WebSocket routers ───────────────────────────────────────────────────────────
app.include_router(camera_ws.router)  # WS /api/ws/camera/{bus_id}
app.include_router(events_ws.router)  # WS /api/ws/events


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root(db: Session = Depends(get_db)):
    events_count = db.query(func.count(Event.event_id)).scalar() or 0
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "events_stored": events_count,
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
