"""
run.py
------
Standalone CLI runner for the Pothole & Road Damage AI module.

Usage examples:
    # Run on default sample video with live preview:
    python run.py --source sample --show

    # Run on webcam 0 at 0.65 confidence:
    python run.py --source 0 --conf 0.65 --show

    # Run headless on a video file and log JSONL events:
    python run.py --source /path/to/road.mp4 --output-log events.jsonl --no-show
"""

import argparse
import json
import sys
from pathlib import Path

from pothole_config import (
    DEFAULT_WEIGHTS,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    SAMPLE_VIDEOS,
    DEFAULT_EVIDENCE_DIR,
)
from pipeline import PotholePipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pothole & Road Damage AI — YOLOv8 Detection & Severity Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        type=str,
        default="sample",
        help="Input source: camera index (e.g. 0), image file, video file, or 'sample' / 'sample_rural'",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=DEFAULT_WEIGHTS,
        help="Path to YOLOv8 weights file",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=CONFIDENCE_THRESHOLD,
        help="Minimum confidence threshold (0.0 to 1.0)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=IOU_THRESHOLD,
        help="NMS IoU threshold",
    )
    parser.add_argument(
        "--show",
        dest="show",
        action="store_true",
        default=False,
        help="Display live annotated OpenCV video window",
    )
    parser.add_argument(
        "--no-show",
        dest="show",
        action="store_false",
        help="Disable GUI preview (headless mode)",
    )
    parser.add_argument(
        "--output-log",
        type=str,
        default="",
        help="Path to save output event JSONL stream (e.g. detected_potholes.jsonl)",
    )
    parser.add_argument(
        "--save-evidence",
        action="store_true",
        default=True,
        help="Save annotated evidence frames to evidence directory",
    )
    parser.add_argument(
        "--evidence-dir",
        type=str,
        default=str(DEFAULT_EVIDENCE_DIR),
        help="Directory to save evidence frames",
    )
    parser.add_argument(
        "--emit-interval",
        type=float,
        default=1.0,
        help="Minimum seconds between event emissions",
    )
    return parser.parse_args()


def resolve_source(source_arg: str):
    if source_arg == "sample":
        sample_path = SAMPLE_VIDEOS.get("city")
        if sample_path and sample_path.exists():
            return str(sample_path)
    elif source_arg == "sample_rural":
        sample_path = SAMPLE_VIDEOS.get("rural")
        if sample_path and sample_path.exists():
            return str(sample_path)
    elif source_arg.isdigit():
        return int(source_arg)
    return source_arg


def main():
    args = parse_args()
    resolved_source = resolve_source(args.source)

    print("=" * 65)
    print("  AI-POWERED URBAN INTELLIGENCE — POTHOLE & ROAD DAMAGE AI")
    print("=" * 65)
    print(f" Source          : {resolved_source}")
    print(f" Weights         : {args.weights}")
    print(f" Confidence Min  : {args.conf:.2f}")
    print(f" Severity Logic  : Explainable Area & Width Ratio")
    print(f" Preview GUI     : {'Enabled' if args.show else 'Disabled (Headless)'}")
    print(f" Evidence Dir    : {args.evidence_dir}")
    print("=" * 65 + "\n")

    pipeline = PotholePipeline(
        source=resolved_source,
        model_path=args.weights,
        conf_thresh=args.conf,
        iou_thresh=args.iou,
        show=args.show,
        save_evidence=args.save_evidence,
        evidence_dir=args.evidence_dir,
        emit_interval_seconds=args.emit_interval,
    )

    log_file = None
    if args.output_log:
        log_file = open(args.output_log, "a", encoding="utf-8")
        print(f"[Pothole AI] Streaming event records to: {args.output_log}")

    event_count = 0
    try:
        for event in pipeline.run():
            event_count += 1
            json_str = json.dumps(event)
            print(f"[EVENT #{event_count:03d}] {event['event_type'].upper()} | Conf: {event['confidence']:.2f} | Severity: {event['severity'].upper()} | Frame: {event['source_frame']}")
            if log_file:
                log_file.write(json_str + "\n")
                log_file.flush()

    except KeyboardInterrupt:
        print("\n[Pothole AI] Pipeline stopped by operator.")
    finally:
        if log_file:
            log_file.close()
        print(f"\n[Pothole AI] Total verified road damage events emitted: {event_count}")


if __name__ == "__main__":
    main()
