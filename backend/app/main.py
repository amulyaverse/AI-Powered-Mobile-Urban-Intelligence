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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.models import Bus, Event, Hotspot, SystemAlert   # noqa — ensure models are registered
from app.seed import run_seed
from app.routers import events, buses, analytics, hotspots

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data on startup."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_seed(db)
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

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(events.router)
app.include_router(buses.router)
app.include_router(analytics.router)
app.include_router(hotspots.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
