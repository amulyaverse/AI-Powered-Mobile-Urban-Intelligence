from __future__ import annotations
import torch
from ultralytics import YOLO

# Fix for PyTorch 2.6+ compatibility with some YOLO weights
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

class PotholeDetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.25):
        self.model = YOLO(model_path)
        self.conf = conf

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        raw_boxes = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf >= self.conf:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                raw_boxes.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'conf': conf, 'class_name': class_name
                })
        return raw_boxes

