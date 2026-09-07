"""
clear_db.py
-----------
Utility script to completely wipe all records from the database,
leaving all tables completely empty (0 rows).

Usage:
    python backend/clear_db.py
"""

from __future__ import annotations
import sys
import os

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.bus import Bus
from app.models.event import Event
from app.models.hotspot import Hotspot
from app.models.alert import SystemAlert
from app.models.ws_session import WsSession
from sqlalchemy import text, inspect


def clear_database():
    print("[Clear] Connecting to database...")
    # Ensure tables exist first
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[Clear] Deleting all records from tables...")
        # Delete in order of dependencies (child records before parent records)
        db.query(WsSession).delete()
        db.query(SystemAlert).delete()
        db.query(Event).delete()
        db.query(Hotspot).delete()
        db.query(Bus).delete()
        db.commit()

        # Reset SQLite auto-increment counters if applicable
        try:
            db.execute(text("DELETE FROM sqlite_sequence"))
            db.commit()
        except Exception:
            pass

        print("[Clear] Verifying record counts:")
        inspector = inspect(engine)
        for table in inspector.get_table_names():
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"   * {table}: {count} rows")

        print("\n[Success] Database has been completely cleared. All tables are empty (0 rows).")
    except Exception as e:
        db.rollback()
        print(f"[Error] Failed to clear database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_database()
