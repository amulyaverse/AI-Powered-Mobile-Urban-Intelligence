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
    inspector = inspect(eng)
    if "events" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("events")}
        with eng.connect() as conn:
            if "source_frame" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN source_frame INTEGER"))
            if "frame_coverage_ratio" not in columns:
                conn.execute(text("ALTER TABLE events ADD COLUMN frame_coverage_ratio FLOAT"))
            conn.commit()

