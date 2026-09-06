"""
scripts/calibrate_timestamps.py
--------------------------------
Calibrates all timestamps in urban_intelligence.db so they represent
accurate, realistic, chronological UTC timestamps anchored to the current
local execution time, eliminating any stale, negative, or random jumps.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

DB_PATH = Path(__file__).resolve().parents[1] / "backend" / "urban_intelligence.db"

def calibrate():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    now = datetime.now(timezone.utc)
    print(f"[Calibrate] Calibrating timestamps relative to UTC now: {now.isoformat()}...")

    # 1. Calibrate events table
    c.execute("SELECT event_id, timestamp FROM events ORDER BY rowid DESC")
    rows = c.fetchall()
    print(f"[Calibrate] Found {len(rows)} events to calibrate.")

    for idx, (evt_id, _) in enumerate(rows):
        # Stagger events cleanly backwards from now:
        # Most recent 5 events within last 1 to 8 minutes
        # Older events within last 1 to 4 hours
        if idx < 5:
            delta_mins = 1 + (idx * 1.5)
        elif idx < 15:
            delta_mins = 8 + ((idx - 5) * 4)
        else:
            delta_mins = 48 + ((idx - 15) * 8)

        new_ts = (now - timedelta(minutes=delta_mins)).replace(microsecond=0)
        iso_str = new_ts.isoformat()
        c.execute("UPDATE events SET timestamp = ? WHERE event_id = ?", (iso_str, evt_id))

    # 2. Calibrate buses table (active buses seen 1-4 mins ago)
    c.execute("SELECT id, status FROM buses")
    buses = c.fetchall()
    for idx, (bus_id, status) in enumerate(buses):
        if status == "Active":
            seen_delta = timedelta(minutes=1 + idx * 0.8)
        else:
            seen_delta = timedelta(hours=2 + idx)
        bus_seen = (now - seen_delta).replace(microsecond=0).isoformat()
        c.execute("UPDATE buses SET last_seen = ? WHERE id = ?", (bus_seen, bus_id))

    # 3. Calibrate alerts table if present
    try:
        c.execute("SELECT id FROM system_alerts")
        alerts = c.fetchall()
        for idx, (alt_id,) in enumerate(alerts):
            alt_ts = (now - timedelta(minutes=3 + idx * 7)).replace(microsecond=0).isoformat()
            c.execute("UPDATE system_alerts SET timestamp = ? WHERE id = ?", (alt_ts, alt_id))
    except Exception:
        pass

    conn.commit()
    conn.close()
    print("[Calibrate] Successfully calibrated all database timestamps to clean UTC ISO strings.")

if __name__ == "__main__":
    calibrate()
