#!/usr/bin/env python3
"""
scripts/stream_camera.py
-------------------------
Edge Camera Streamer & Simulator.

Captures frames from a local webcam, video file, or synthetic generator,
encodes them to JPEG, and streams them over WebSocket to the backend:
    WS ws://{host}/api/ws/camera/{bus_id}?lat={lat}&lng={lng}&mode={mode}

The backend runs server-side YOLO inference at 2 FPS and broadcasts
results live to all connected frontend dashboards.

Usage:
    # 1. Stream from laptop webcam (camera index 0):
    python scripts/stream_camera.py --bus BUS_021 --mode traffic --source 0

    # 2. Stream from a recorded traffic / road video file:
    python scripts/stream_camera.py --bus BUS_021 --mode traffic --video path/to/sample.mp4

    # 3. Stream synthetic test frames (no webcam or video required):
    python scripts/stream_camera.py --bus BUS_021 --mode traffic --synthetic
"""

import argparse
import asyncio
import json
import sys
import time
from urllib.parse import urlencode

try:
    import cv2
    import numpy as np
except ImportError:
    print("[ERROR] OpenCV and NumPy are required. Install with: pip install opencv-python numpy")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("[ERROR] websockets is required. Install with: pip install websockets")
    sys.exit(1)


def generate_synthetic_frame(frame_num: int, mode: str = "traffic") -> np.ndarray:
    """
    Generate an artificial 640x480 frame for headless or camera-free testing.
    Draws a simulated asphalt roadway with moving shapes.
    """
    # Dark asphalt road background
    img = np.full((480, 640, 3), 45, dtype=np.uint8)

    # Road edges and lane markings
    cv2.line(img, (100, 0), (50, 480), (180, 180, 180), 3)
    cv2.line(img, (540, 0), (590, 480), (180, 180, 180), 3)

    # Dashed center yellow line
    offset = (frame_num * 15) % 80
    for y in range(offset, 480, 80):
        cv2.line(img, (320, y), (320, min(y + 40, 480)), (0, 215, 255), 3)

    if mode == "traffic":
        # Draw moving car shape
        car_y = (frame_num * 18) % 400 + 40
        cv2.rectangle(img, (220, car_y), (300, car_y + 90), (0, 0, 200), -1)
        cv2.putText(img, "TEST VEHICLE", (215, car_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Draw a second moving bike shape
        bike_y = ((frame_num * 24) + 120) % 400 + 40
        cv2.rectangle(img, (370, bike_y), (410, bike_y + 50), (200, 150, 0), -1)
    else:
        # Pothole mode: draw dark oval defect on asphalt
        cv2.ellipse(img, (300, 280), (45, 25), 0, 0, 360, (20, 20, 20), -1)
        cv2.ellipse(img, (300, 280), (45, 25), 0, 0, 360, (70, 70, 70), 2)
        cv2.putText(img, "ROAD DEFECT", (260, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)

    # Timestamp overlay
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, f"SIMULATED FEED | {timestamp_str} | Frame #{frame_num}",
                (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    return img


async def stream_frames(args):
    params = {
        "lat": args.lat,
        "lng": args.lng,
        "mode": args.mode,
    }
    ws_uri = f"ws://{args.host}/api/ws/camera/{args.bus}?{urlencode(params)}"

    print("=" * 65)
    print(f"  AI Urban Intelligence — Edge Camera Streamer")
    print("=" * 65)
    print(f"  Bus ID       : {args.bus}")
    print(f"  Inference    : {args.mode.upper()}")
    print(f"  Target Rate  : {args.fps} FPS")
    print(f"  Target URI   : {ws_uri}")
    print(f"  Source       : {'Synthetic' if args.synthetic else args.video or f'Webcam index {args.source}'}")
    print("=" * 65)

    cap = None
    if not args.synthetic:
        if args.video:
            cap = cv2.VideoCapture(args.video)
            if not cap.isOpened():
                print(f"[ERROR] Could not open video file: {args.video}")
                print("[INFO] Falling back to synthetic test frame generator.")
                args.synthetic = True
        else:
            try:
                cam_idx = int(args.source)
            except ValueError:
                cam_idx = 0
            cap = cv2.VideoCapture(cam_idx)
            if not cap.isOpened():
                print(f"[WARN] Webcam index {cam_idx} not available.")
                print("[INFO] Switching to synthetic test frame generator.")
                args.synthetic = True

    print(f"\n[1/2] Connecting to WebSocket at {ws_uri} ...")
    try:
        async with websockets.connect(ws_uri) as ws:
            print("[2/2] WebSocket connected successfully! Streaming frames...\n")
            frame_index = 0
            interval = 1.0 / max(0.1, args.fps)

            while True:
                start_time = time.monotonic()
                frame_index += 1

                # 1. Grab Frame
                if args.synthetic or cap is None:
                    frame = generate_synthetic_frame(frame_index, mode=args.mode)
                else:
                    ret, frame = cap.read()
                    if not ret:
                        if args.video:
                            # Loop video
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                        if not ret:
                            print("[WARN] Camera frame read failed. Generating synthetic frame.")
                            frame = generate_synthetic_frame(frame_index, mode=args.mode)

                # Resize to standard 640x480 if needed
                if frame.shape[1] != 640 or frame.shape[0] != 480:
                    frame = cv2.resize(frame, (640, 480))

                # 2. Encode to JPEG
                success, jpeg_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not success:
                    print(f"[WARN] Failed to encode frame #{frame_index}")
                    continue

                raw_bytes = jpeg_buf.tobytes()

                # 3. Send raw JPEG bytes
                t_send = time.monotonic()
                await ws.send(raw_bytes)

                # 4. Receive backend response
                try:
                    resp_str = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    rtt_ms = (time.monotonic() - t_send) * 1000
                    resp_data = json.loads(resp_str)

                    status = resp_data.get("status")
                    if status == "frame_skipped":
                        print(f"  [#{frame_index:04d}] Frame skipped by sampler (<500ms interval)")
                    elif status == "no_detection":
                        print(f"  [#{frame_index:04d}] Inference: 0 detections ({rtt_ms:.0f}ms)")
                    elif status == "suppressed":
                        print(f"  [#{frame_index:04d}] Event suppressed (temporal deduplication) ({rtt_ms:.0f}ms)")
                    else:
                        evt_id = resp_data.get("event_id", "LIVE")
                        evt_type = resp_data.get("event_type", "detection")
                        conf = resp_data.get("confidence", 0.0)
                        density = resp_data.get("density", "")
                        cars = resp_data.get("car_count", 0)
                        bikes = resp_data.get("bike_count", 0)
                        buses = resp_data.get("bus_count", 0)

                        details = f"Density: {density} (Cars: {cars}, Bikes: {bikes}, Buses: {buses})" if density else f"Confidence: {conf*100:.1f}%"
                        print(f"  \033[92m[#{frame_index:04d}]\033[0m \033[1m{evt_type.upper()}\033[0m -> {details} | RTT: {rtt_ms:.0f}ms | ID: {evt_id}")

                except asyncio.TimeoutError:
                    print(f"  [#{frame_index:04d}] Server ack timed out (>2s)")
                except Exception as e:
                    print(f"  [#{frame_index:04d}] Response parse error: {e}")

                # Sleep to maintain desired FPS
                elapsed = time.monotonic() - start_time
                sleep_time = max(0.0, interval - elapsed)
                await asyncio.sleep(sleep_time)

    except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidURI) as e:
        print(f"\n[ERROR] Connection closed or failed: {e}")
    except ConnectionRefusedError:
        print(f"\n[ERROR] Connection refused! Is the FastAPI backend running on {args.host}?")
        print("        Start it with: cd backend && uvicorn app.main:app --reload --port 8000")
    except KeyboardInterrupt:
        print(f"\n[INFO] Streaming stopped by user after {frame_index} frames.")
    finally:
        if cap is not None:
            cap.release()
        print("[INFO] Camera stream cleaned up.")


def main():
    parser = argparse.ArgumentParser(
        description="Stream camera frames to AI-Powered Urban Intelligence WebSocket endpoint."
    )
    parser.add_argument("--bus", default="BUS_021", help="Bus ID identifier (default: BUS_021)")
    parser.add_argument("--mode", choices=["traffic", "pothole"], default="traffic",
                        help="Inference mode: 'traffic' or 'pothole' (default: traffic)")
    parser.add_argument("--source", default="0", help="Webcam device index (default: 0)")
    parser.add_argument("--video", default=None, help="Path to local video file to loop and stream")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic test frames")
    parser.add_argument("--host", default="localhost:8000", help="FastAPI host:port (default: localhost:8000)")
    parser.add_argument("--lat", type=float, default=28.6139, help="GPS Latitude (default: 28.6139)")
    parser.add_argument("--lng", type=float, default=77.2090, help="GPS Longitude (default: 77.2090)")
    parser.add_argument("--fps", type=float, default=2.0, help="Stream frame rate (default: 2.0 FPS)")

    args = parser.parse_args()

    try:
        asyncio.run(stream_frames(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
