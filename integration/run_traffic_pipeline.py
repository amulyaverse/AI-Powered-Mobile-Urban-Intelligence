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
    - event_type: "vehicle_count" (not "congestion") -- this is what
      unlocks car_count/bike_count/density fields on Arjun's backend
      schema and inference engine, since those are only populated for
      vehicle_count events.
    - severity: his `density` field (LOW/MEDIUM/HIGH/CRITICAL) already
      uses the exact same words as the schema's `severity` field, just
      different case -- so this is a straight .lower(), no judgment call.
    - vehicle_counts / density / density_score / etc: forwarded directly
      so the backend stores the full car/bike/bus/truck breakdown instead
      of discarding it.
    - evidence: his pipeline doesn't save a snapshot image per event
      (only an optional full annotated video via --save), so there's no
      real file to point to yet. Using the frame index as a placeholder.
    - camera_id / latitude / longitude: intentionally left out here --
      event_generator.py already fills in a default camera_id and
      attaches simulated GPS automatically.
    """
    return {
        "event_type": "vehicle_count",
        "confidence": round(event.confidence, 4),
        "severity": event.density.lower(),
        "bus_id": event.bus_id,
        "evidence": f"frame_{event.source_frame}",
        "vehicle_counts": event.vehicle_counts,
        "total_vehicles": event.total_vehicles,
        "density": event.density,
        "density_score": event.density_score,
        "source_frame": event.source_frame,
        "frame_coverage_ratio": event.frame_coverage_ratio,
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
