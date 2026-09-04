"""
run_traffic_pipeline.py
------------------------
Runs Pranav's real TrafficPipeline on a video and feeds every
TrafficEvent it produces through the integration layer to the backend.

This REPLACES fake_traffic_detection() in test_pipeline.py once
Pranav's code is ready to plug in for real.

Usage:
    python integration/run_traffic_pipeline.py --source path/to/video.mp4 --bus-id BUS_021

Make sure the backend is already running (see README_INTEGRATION.md)
before you run this.
"""

import argparse
import sys
from pathlib import Path

# --- import Pranav's pipeline -----------------------------------------
# Adjust this path if his folder is named differently on your machine
# (e.g. "traffic_detection" with an underscore instead of a hyphen --
# we already hit exactly this kind of mismatch once with event-generator,
# so double-check with: Get-ChildItem edge-ai)
TRAFFIC_AI_DIR = Path(__file__).resolve().parents[1] / "edge-ai" / "traffic-detection"
sys.path.append(str(TRAFFIC_AI_DIR))
from pipeline import TrafficPipeline  # noqa: E402

# --- import our integration wrapper ------------------------------------
sys.path.append(str(Path(__file__).resolve().parent / "event-generator"))
from event_generator import process_detection  # noqa: E402


def adapt_traffic_event(event) -> dict:
    """
    Convert Pranav's TrafficEvent dataclass into the dict shape that
    event_generator.process_detection() expects (docs/api/event-schema.md).

    Mapping notes:
    - event_type: his pipeline only produces traffic snapshots, so this
      is always "congestion" -- the closest allowed value in the schema.
    - severity: his `density` field (LOW/MEDIUM/HIGH/CRITICAL) already
      uses the exact same words as the schema's `severity` field, just
      different case -- so this is a straight .lower(), no judgment call.
    - evidence: his pipeline doesn't save a snapshot image per event
      (only an optional full annotated video via --save), so there's no
      real file to point to yet. Using the frame index as a placeholder
      string -- flag this to the team if you want an actual saved frame
      per event later.
    - camera_id / latitude / longitude: intentionally left out here --
      event_generator.py already fills in a default camera_id and
      attaches simulated GPS automatically, so you don't need to supply
      them from Pranav's event.
    """
    return {
        "event_type": "congestion",
        "confidence": round(event.confidence, 4),
        "severity": event.density.lower(),
        "bus_id": event.bus_id,
        "evidence": f"frame_{event.source_frame}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run traffic AI -> integration -> backend")
    parser.add_argument("--source", required=True, help="video file path or camera index (e.g. 0)")
    parser.add_argument("--bus-id", default="BUS_021")
    args = parser.parse_args()

    source: str | int = int(args.source) if args.source.isdigit() else args.source

    pipeline = TrafficPipeline(source=source, bus_id=args.bus_id)

    print(f"Running traffic pipeline on {source!r}, sending events to backend...\n")
    for traffic_event in pipeline.run():
        ai_output = adapt_traffic_event(traffic_event)
        process_detection(ai_output)

    print("\nDone. Check http://localhost:8000/api/events")


if __name__ == "__main__":
    main()
