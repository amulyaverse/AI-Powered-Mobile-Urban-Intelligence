"""
scripts/clear_database.py
-------------------------
Completely clears all tables from urban_intelligence.db, resets auto-increment
sequences, and cleans up temporary test database files and test evidence frames.
"""

import sqlite3
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "backend" / "urban_intelligence.db"
TEST_DB_PATH = ROOT_DIR / "test.db"
EVIDENCE_DIR = ROOT_DIR / "frontend" / "public" / "evidence"

def clear_all():
    print(f"[ClearDB] Connecting to {DB_PATH}...")
    if not DB_PATH.exists():
        print(f"[ClearDB] Error: {DB_PATH} does not exist.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")

    tables = ["events", "hotspots", "system_alerts", "ws_sessions", "buses"]
    counts = {}

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError as e:
            print(f"[ClearDB] Warning on table '{table}': {e}")

    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('events', 'hotspots', 'system_alerts', 'ws_sessions', 'buses')")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("VACUUM;")
    conn.close()

    print("[ClearDB] Rows deleted:")
    for table, count in counts.items():
        print(f"  - {table}: {count} rows deleted (now 0)")

    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
            print(f"[ClearDB] Removed test database: {TEST_DB_PATH.name}")
        except Exception as e:
            print(f"[ClearDB] Could not remove {TEST_DB_PATH}: {e}")

    if EVIDENCE_DIR.exists():
        deleted_evts = 0
        for p in EVIDENCE_DIR.glob("EVT_*.jpg"):
            try:
                p.unlink()
                deleted_evts += 1
            except Exception:
                pass
        print(f"[ClearDB] Removed {deleted_evts} temporary live/test evidence image(s).")

    print("[ClearDB] Database successfully wiped and reset to clean state.")

if __name__ == "__main__":
    clear_all()
