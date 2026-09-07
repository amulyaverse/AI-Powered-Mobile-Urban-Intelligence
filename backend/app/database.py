"""
database.py
-----------
SQLAlchemy engine, session factory, and declarative Base.

Uses DATABASE_URL from config — supports both SQLite (dev) and PostgreSQL (prod).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# SQLite needs connect_args for thread safety in FastAPI
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # Log SQL statements in debug mode
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency — yields a DB session and ensures it is closed
    after the request is complete, even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_db(eng):
    """
    Idempotent, lightweight schema migration helper for SQLite/PostgreSQL.
    Ensures newly added columns exist without requiring manual migration steps.
    """
    from sqlalchemy import inspect, text
    from app.models.ws_session import WsSession  # noqa — ensure table is known
    inspector = inspect(eng)

    # ── events table column additions ─────────────────────────────────────────
    if "events" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("events")}
        with eng.connect() as conn:
            if "source_frame" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN source_frame INTEGER"))
            if "frame_coverage_ratio" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN frame_coverage_ratio FLOAT"))
            if "ws_session_id" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN ws_session_id TEXT"))
            # PR 37 & 40 pothole / road defect columns
            if "bbox" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN bbox TEXT"))
            if "width_ratio" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN width_ratio FLOAT"))
            if "area_ratio" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN area_ratio FLOAT"))
            if "severity_method" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN severity_method VARCHAR(30)"))
            if "surface_condition" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN surface_condition VARCHAR(50)"))
            conn.commit()

        # Normalize legacy ISO timestamps with 'T' in SQLite
        if settings.DATABASE_URL.startswith("sqlite"):
            with eng.connect() as conn:
                conn.execute(text("UPDATE events SET timestamp = strftime('%Y-%m-%d %H:%M:%S', timestamp) WHERE timestamp LIKE '%T%'"))
                conn.commit()

    # ── ws_sessions table (created automatically by Base.metadata.create_all,
    #    but guard here for databases that were initialised before this table
    #    was added to the model registry) ──────────────────────────────────────
    if "ws_sessions" not in inspector.get_table_names():
        WsSession.__table__.create(eng)

