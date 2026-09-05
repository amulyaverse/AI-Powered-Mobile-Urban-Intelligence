import cv2
import json
import time
import torch
import os
from ultralytics import YOLO

# Fix for PyTorch 2.6+ compatibility with some YOLO weights
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

# ---------------------------------------------------------
# APPROACH B: Severity based on Depth-Aware Scaling (Perspective)
# ---------------------------------------------------------

def determine_severity_b(box_width, box_y_center, frame_width, frame_height):
    y_norm = box_y_center / frame_height
    if y_norm < 0.3:
        y_norm = 0.3 
        
    perspective_multiplier = 1.0 / y_norm
    adjusted_width = box_width * perspective_multiplier
    adjusted_width_percentage = adjusted_width / frame_width
    
    if adjusted_width_percentage > 0.30:
        return "HIGH"
    elif adjusted_width_percentage > 0.15:
        return "MEDIUM"
    else:
        return "LOW"

def main():
    # ---------------------------------------------------------
    # PC-TAILORED SETTINGS (Hardcoded for easy "Run" in VS Code)
    # ---------------------------------------------------------
    video_source = r"E:\Application Dev\VS Code files\Git\Pothole_Road_Condition_Model\ruralRoad_potHoles.mp4"
    model_path = r"E:\Application Dev\VS Code files\Git\Pothole_Road_Condition_Model\edge_inference\best_huggingface.pt"
    confidence_threshold = 0.60
    output_log_file = "detected_events_approach_b.jsonl"
    
    print(f"Loading model from {model_path}...")
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source {video_source}")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    log_file = open(output_log_file, 'a')
    print(f"Logging events to {output_log_file}")
    print(f"Starting Inference. Press 'q' in preview window to quit.")
    
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
            
            if conf >= confidence_threshold:
                severity = determine_severity_b(float(w), float(y_c), frame_width, frame_height)
                
                # Format event for backend
                event_data = {
                    "event_type": class_name,
                    "confidence": round(conf, 2),
                    "severity": severity,
                    "bus_id": "BUS_01",
                    "camera_id": "CAM_FRONT",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                event_output = f"{class_name.capitalize()} | Confidence: {conf*100:.0f}% | Severity: {severity}"
                
                # Log to file
                log_file.write(json.dumps(event_data) + "\n")
                
                # Draw on frame
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, event_output, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Show preview window
        cv2.imshow("Pothole Detection - Approach B", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    log_file.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

