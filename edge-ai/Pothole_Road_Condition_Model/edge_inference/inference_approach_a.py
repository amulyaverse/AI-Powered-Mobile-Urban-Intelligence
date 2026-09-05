import cv2
import argparse
import json
import time
import torch
from ultralytics import YOLO

# Fix for PyTorch 2.6+ compatibility with some YOLO weights
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

# ---------------------------------------------------------
# APPROACH A: Severity based on Box Width relative to Frame
# ---------------------------------------------------------

def determine_severity_a(box_width, frame_width):
    width_percentage = box_width / frame_width
    if width_percentage > 0.25:
        return "HIGH"
    elif width_percentage > 0.10:
        return "MEDIUM"
    else:
        return "LOW"

def main():
    parser = argparse.ArgumentParser(description="Pothole Detection - Approach A (Width Heuristic)")
    parser.add_argument("--source", type=str, default="0", help="Video file path or camera index (default: 0)")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Path to YOLO weights file")
    parser.add_argument("--conf", type=float, default=0.50, help="Confidence threshold (default: 0.50)")
    parser.add_argument("--output_log", type=str, default="", help="Path to save event JSON logs (e.g., output.jsonl)")
    parser.add_argument("--no-preview", action="store_true", help="Disable the live video preview window")
    
    args = parser.parse_args()

    # Determine if source is an integer (camera index) or a string (file path)
    if args.source.isdigit():
        video_source = int(args.source)
    else:
        video_source = args.source

    print(f"Loading model from {args.weights}...")
    model = YOLO(args.weights)

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source {args.source}")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    # Open log file if specified
    log_file = None
    if args.output_log:
        log_file = open(args.output_log, 'a')
        print(f"Logging events to {args.output_log}")

    print(f"Starting Inference with Conf >= {args.conf}. Press 'q' in preview window to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video stream.")
            break

        # Run inference
        results = model(frame, verbose=False)[0]

        for box in results.boxes:
            x_c, y_c, w, h = box.xywh[0]
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id] # Dynamically get the class name
            
            if conf >= args.conf:
                severity = determine_severity_a(float(w), frame_width)
                
                # Format event for backend
                event_data = {
                    "event_type": class_name,
                    "confidence": round(conf, 2),
                    "severity": severity,
                    "bus_id": "BUS_01", # Placeholder
                    "camera_id": "CAM_FRONT",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                event_output = f"{class_name.capitalize()} | Confidence: {conf*100:.0f}% | Severity: {severity}"
                print(event_output)
                
                # Log to file if requested
                if log_file:
                    log_file.write(json.dumps(event_data) + "\n")
                
                # Draw if preview is enabled
                if not args.no_preview:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, event_output, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Show preview window
        if not args.no_preview:
            cv2.imshow("Pothole Detection - Approach A", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    if log_file:
        log_file.close()
    if not args.no_preview:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
