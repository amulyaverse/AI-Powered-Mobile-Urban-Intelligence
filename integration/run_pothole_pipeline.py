"""
run_pothole_pipeline.py
-----------------------
Runs the real Pothole & Road Damage Pipeline on a video/camera feed
and feeds every detected defect through the integration layer to the FastAPI backend.

Usage:
    python integration/run_pothole_pipeline.py --source edge-ai/Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --bus-id BUS_021 --show
"""

import argparse
import sys
from pathlib import Path

# --- import Pothole Pipeline with multi-directory fallback resolution ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EDGE_AI_DIR = PROJECT_ROOT / "edge-ai"
CANDIDATE_DIRS = [
    EDGE_AI_DIR / "pothole-latest" / "Pothole_Road_Condition_Model",
    EDGE_AI_DIR / "Pothole_Road_Condition_Model",
    EDGE_AI_DIR / "pothole-detection",
    EDGE_AI_DIR / "pothole_Old",
]

PotholePipeline = None
last_import_error = None

for candidate in CANDIDATE_DIRS:
    if candidate.exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        try:
            from pothole_pipeline import PotholePipeline
            break
        except ImportError as e:
            last_import_error = e
            try:
                from pipeline import PotholePipeline
                break
            except ImportError as e2:
                last_import_error = e2
                continue

if PotholePipeline is None:
    raise ImportError(
        f"Could not import PotholePipeline from any candidate directory: {[str(d) for d in CANDIDATE_DIRS]}. "
        f"Underlying error: {last_import_error}"
    )

# --- import integration layer wrapper -----------------------------------------
sys.path.append(str(Path(__file__).resolve().parent / "event-generator"))
from event_generator import process_detection  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pothole AI -> integration -> backend")
    parser.add_argument("--source", required=True, help="video file path, image path, or camera index (e.g. 0)")
    parser.add_argument("--weights", default="edge-ai/pothole-latest/Pothole_Road_Condition_Model/best_2.pt", help="Path to pothole YOLO weights")
    parser.add_argument("--conf", type=float, default=0.65, help="Confidence threshold (default: 0.65)")
    parser.add_argument("--bus-id", default="BUS_021", help="Reporting bus ID")
    parser.add_argument("--camera-id", default="CAM_FRONT", help="Reporting camera ID")
    parser.add_argument("--no-show", action="store_true", help="Disable preview window")
    parser.add_argument("--save-evidence", action="store_true", default=True, help="Save evidence frames")
    args = parser.parse_args()

    source: str | int = int(args.source) if args.source.isdigit() else args.source

    # Support multiple constructor parameter conventions
    try:
        pipeline = PotholePipeline(
            source=source,
            model_name=args.weights,
            conf=args.conf,
            show=not args.no_show,
            bus_id=args.bus_id,
            camera_id=args.camera_id,
        )
    except TypeError:
        try:
            pipeline = PotholePipeline(
                source=source,
                model_path=args.weights,
                conf_thresh=args.conf,
                show=not args.no_show,
                save_evidence=args.save_evidence,
            )
        except TypeError:
            pipeline = PotholePipeline(source=source)

    print(f"Running Pothole AI pipeline on {source!r} (bus={args.bus_id}, conf>={args.conf}), streaming events to backend...\n")

    event_count = 0
    for raw_output in pipeline.run():
        if hasattr(raw_output, "__dict__"):
            ai_output = dict(raw_output.__dict__)
        elif isinstance(raw_output, dict):
            ai_output = dict(raw_output)
        else:
            continue

        # Skip deletion/healing notifications in the standard detection ingestion channel
        if ai_output.get("action") == "DELETE" or "resolved" in str(ai_output.get("event_type", "")).lower():
            continue

        # Normalise schema
        raw_type = str(ai_output.get("event_type", "pothole")).lower()
        if "defect" in raw_type or "crack" in raw_type:
            event_type = "road_defect"
        else:
            event_type = "pothole"

        raw_sev = str(ai_output.get("severity", "medium")).lower()
        if raw_sev in ("very high", "critical"):
            severity = "high"
        elif raw_sev in ("high", "medium", "low"):
            severity = raw_sev
        else:
            severity = "medium"

        ai_output["event_type"] = event_type
        ai_output["severity"] = severity
        ai_output["confidence"] = float(ai_output.get("confidence", args.conf))
        ai_output["bus_id"] = args.bus_id
        ai_output["camera_id"] = args.camera_id

        event_count += 1
        process_detection(ai_output)

    print(f"\nDone. Streamed {event_count} pothole event(s) to backend.")
    print("Check events at http://localhost:8000/api/events or http://localhost:8000/api/hotspots")


if __name__ == "__main__":
    main()
