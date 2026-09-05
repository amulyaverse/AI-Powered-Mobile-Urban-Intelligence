import cv2
import time
import torch
from typing import Generator
from ultralytics import YOLO

# Fix for PyTorch 2.6+ compatibility
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

class PotholePipeline:
    """
    Pothole AI Pipeline.
    Designed to mimic the architecture of the TrafficPipeline so it can be 
    plugged directly into the integration/event-generator layer.
    """
    def __init__(self, source: str | int = 0, model_path: str = "yolov8n.pt", conf_thresh: float = 0.50, show: bool = True):
        self.source = source
        self.conf_thresh = conf_thresh
        self.show = show
        
        print(f"[PotholePipeline] Loading model from {model_path}...")
        self.model = YOLO(model_path)

    def determine_severity(self, box_width, frame_width):
        """Uses Approach A: Width Heuristic"""
        width_percentage = box_width / frame_width
        if width_percentage > 0.25:
            return "high"
        elif width_percentage > 0.10:
            return "medium"
        else:
            return "low"

    def run(self) -> Generator[dict, None, None]:
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"[PotholePipeline] Cannot open source: {self.source}")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        print(f"[PotholePipeline] Starting inference on {self.source}")
        
        # To avoid spamming the backend with 30 events per second for the same pothole,
        # we will only yield an event once every few frames (or if we had a tracker, once per track).
        # For simplicity in this prototype, we'll emit 1 frame per second.
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frames_per_emit = max(1, int(fps)) 
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                results = self.model(frame, verbose=False)[0]
                
                # Check for detections
                highest_severity_in_frame = None
                best_conf = 0.0
                best_class_name = "pothole"

                for box in results.boxes:
                    x_c, y_c, w, h = box.xywh[0]
                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]

                    if conf >= self.conf_thresh:
                        severity = self.determine_severity(float(w), frame_width)
                        
                        # Keep track of the worst defect in this frame
                        if highest_severity_in_frame is None or severity == "high":
                            highest_severity_in_frame = severity
                            best_conf = conf
                            best_class_name = class_name
                            
                        # Draw if showing
                        if self.show:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(frame, f"{class_name} {severity.upper()}", (x1, y1 - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                if self.show:
                    cv2.imshow("Pothole AI Pipeline", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Yield an event every 1 second of video to the integration layer
                if frame_idx % frames_per_emit == 0 and highest_severity_in_frame is not None:
                    # Output matching the integration layer contract
                    ai_output = {
                        "event_type": best_class_name,
                        "confidence": best_conf,
                        "severity": highest_severity_in_frame,
                        "evidence": f"frame_{frame_idx}"
                    }
                    yield ai_output

                frame_idx += 1

        finally:
            cap.release()
            if self.show:
                cv2.destroyAllWindows()

