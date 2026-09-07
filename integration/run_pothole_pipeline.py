"""
run_pothole_pipeline.py
-----------------------
Runs Abhinandan's real Pothole & Road Damage Pipeline on a video/camera feed
and feeds every detected defect through the integration layer to the FastAPI backend.

Usage:
    python integration/run_pothole_pipeline.py --source edge-ai/Pothole_Road_Condition_Model/cityRoad_potHoles.mp4 --bus-id BUS_021 --show
"""

import argparse
import sys
from pathlib import Path

# --- import Pothole Pipeline from edge-ai/pothole-detection (with fallback) ---
POTHOLE_AI_DIR = Path(__file__).resolve().parents[1] / "edge-ai" / "pothole-detection"
if not (POTHOLE_AI_DIR / "pipeline.py").exists():
    POTHOLE_AI_DIR = Path(__file__).resolve().parents[1] / "edge-ai" / "Pothole_Road_Condition_Model"

sys.path.insert(0, str(POTHOLE_AI_DIR))
from pipeline import PotholePipeline  # noqa: E402

# --- import integration layer wrapper -----------------------------------------
sys.path.append(str(Path(__file__).resolve().parent / "event-generator"))
from event_generator import process_detection  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pothole AI -> integration -> backend")
    parser.add_argument("--source", required=True, help="video file path, image path, or camera index (e.g. 0)")
    parser.add_argument("--weights", default="yolov8n.pt", help="Path to pothole YOLO weights")
    parser.add_argument("--conf", type=float, default=0.65, help="Confidence threshold (default: 0.65)")
    parser.add_argument("--bus-id", default="BUS_021", help="Reporting bus ID")
    parser.add_argument("--camera-id", default="CAM_FRONT", help="Reporting camera ID")
    parser.add_argument("--no-show", action="store_true", help="Disable preview window")
    parser.add_argument("--save-evidence", action="store_true", default=True, help="Save evidence frames")
    args = parser.parse_args()

    source: str | int = int(args.source) if args.source.isdigit() else args.source

    pipeline = PotholePipeline(
        source=source,
        model_path=args.weights,
        conf_thresh=args.conf,
        show=not args.no_show,
        save_evidence=args.save_evidence,
    )

    print(f"Running Pothole AI pipeline on {source!r} (bus={args.bus_id}, conf>={args.conf}), streaming events to backend...\n")

    event_count = 0
    for ai_output in pipeline.run():
        event_count += 1
        # Attach bus_id and camera_id for integration layer
        ai_output["bus_id"] = args.bus_id
        ai_output["camera_id"] = args.camera_id
        process_detection(ai_output)

    print(f"\nDone. Streamed {event_count} pothole event(s) to backend.")
    print("Check events at http://localhost:8000/api/events or http://localhost:8000/api/hotspots")


if __name__ == "__main__":
    main()
