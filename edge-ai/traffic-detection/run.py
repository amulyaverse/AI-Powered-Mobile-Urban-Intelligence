"""
run.py
------
CLI entry point for the Vehicle AI pipeline.

Examples:
    # Run on a video file (display window + save output)
    python run.py --source traffic.mp4 --show --save output.mp4

    # Webcam (camera index 0)
    python run.py --source 0 --show

    # Headless (no window) — just print events to stdout
    python run.py --source traffic.mp4

    # Use a larger model for better accuracy
    python run.py --source traffic.mp4 --model yolov8m --show

    # Specify bus ID (for backend event tagging)
    python run.py --source traffic.mp4 --bus-id BUS-042 --show
"""

import argparse
import json
import sys
import os

# Add parent dir to path if running from anywhere
sys.path.insert(0, os.path.dirname(__file__))

from pipeline import TrafficPipeline
from config import MODEL_NAME, CONFIDENCE_THRESHOLD, IOU_THRESHOLD, EVENT_EMIT_INTERVAL_SEC


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vehicle AI — Traffic Detection Pipeline (SIH 2026)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source", "-s",
        type=str, default="0",
        help="Video file path or camera index (default: 0 = webcam)",
    )
    parser.add_argument(
        "--model", "-m",
        type=str, default=MODEL_NAME,
        choices=["yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"],
        help=f"YOLOv8 model variant (default: {MODEL_NAME})",
    )
    parser.add_argument(
        "--conf", "-c",
        type=float, default=CONFIDENCE_THRESHOLD,
        help=f"Detection confidence threshold (default: {CONFIDENCE_THRESHOLD})",
    )
    parser.add_argument(
        "--iou",
        type=float, default=IOU_THRESHOLD,
        help=f"NMS IoU threshold (default: {IOU_THRESHOLD})",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display annotated video window",
    )
    parser.add_argument(
        "--save", "-o",
        type=str, default=None, metavar="OUTPUT.mp4",
        help="Save annotated video to file",
    )
    parser.add_argument(
        "--bus-id",
        type=str, default="BUS-001",
        help="Bus / device identifier (embedded in every event)",
    )
    parser.add_argument(
        "--emit-interval",
        type=float, default=EVENT_EMIT_INTERVAL_SEC,
        help=f"Emit a TrafficEvent every N seconds (default: {EVENT_EMIT_INTERVAL_SEC})",
    )
    parser.add_argument(
        "--json-out",
        type=str, default=None, metavar="EVENTS.jsonl",
        help="Write events as JSONL to a file (one JSON object per line)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Source: convert to int if it's a camera index
    source: str | int = args.source
    if source.isdigit():
        source = int(source)

    print("=" * 60)
    print("  Vehicle AI — Traffic Detection  |  SIH 2026")
    print("=" * 60)
    print(f"  Source     : {source}")
    print(f"  Model      : {args.model}")
    print(f"  Confidence : {args.conf}")
    print(f"  IoU        : {args.iou}")
    print(f"  Bus ID     : {args.bus_id}")
    print(f"  Show       : {args.show}")
    print(f"  Save to    : {args.save or 'disabled'}")
    print(f"  JSON out   : {args.json_out or 'disabled'}")
    print("=" * 60)
    print()

    pipeline = TrafficPipeline(
        source=source,
        model_name=args.model,
        conf=args.conf,
        iou=args.iou,
        show=args.show,
        save_path=args.save,
        bus_id=args.bus_id,
        emit_interval=args.emit_interval,
    )

    jsonl_file = None
    if args.json_out:
        jsonl_file = open(args.json_out, "w", encoding="utf-8")

    try:
        for event in pipeline.run():
            if jsonl_file:
                jsonl_file.write(event.to_json(indent=None) + "\n")
                jsonl_file.flush()
    finally:
        if jsonl_file:
            jsonl_file.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
