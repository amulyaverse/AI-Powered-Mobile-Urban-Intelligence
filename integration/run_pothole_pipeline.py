import argparse
import sys
from pathlib import Path

# --- import Abhinandan's Pothole pipeline ------------------------------
POTHOLE_AI_DIR = Path(__file__).resolve().parents[1] / "edge-ai" / "Pothole_Road_Condition_Model"
sys.path.append(str(POTHOLE_AI_DIR))
from pipeline import PotholePipeline  # noqa: E402

# --- import our integration wrapper ------------------------------------
sys.path.append(str(Path(__file__).resolve().parent / "event-generator"))
from event_generator import process_detection  # noqa: E402

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Pothole AI -> integration -> backend")
    parser.add_argument("--source", required=True, help="video file path or camera index (e.g. 0)")
    parser.add_argument("--weights", default="yolov8n.pt", help="Path to pothole YOLO weights")
    parser.add_argument("--conf", type=float, default=0.50, help="Confidence threshold")
    parser.add_argument("--no-show", action="store_true", help="Disable preview window")
    args = parser.parse_args()

    source: str | int = int(args.source) if args.source.isdigit() else args.source

    pipeline = PotholePipeline(
        source=source, 
        model_path=args.weights, 
        conf_thresh=args.conf, 
        show=not args.no_show
    )

    print(f"Running Pothole pipeline on {source!r}, sending events to backend...\n")
    
    # Loop over the generated events
    for ai_output in pipeline.run():
        # The AI module yields a dict exactly matching the integration schema!
        # Hand it off to Parminder's event generator
        process_detection(ai_output)

    print("\nDone. Check http://localhost:8000/api/events")

if __name__ == "__main__":
    main()

