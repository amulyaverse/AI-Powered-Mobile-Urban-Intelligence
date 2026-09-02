"""
config.py
---------
Central configuration for the Vehicle AI pipeline.
Adjust thresholds, model paths, and class mappings here.
"""

# ─── Model ────────────────────────────────────────────────────────────────────
# Options: "yolov8n", "yolov8s", "yolov8m", "yolov8l", "yolov8x"
# Nano (n) is fastest — good for edge devices (Raspberry Pi / Jetson Nano)
# Medium (m) is a good accuracy/speed balance on laptops
MODEL_NAME = "yolov8n"          # pretrained COCO weights, auto-downloaded on first run
CONFIDENCE_THRESHOLD = 0.40     # minimum detection confidence (0–1)
IOU_THRESHOLD = 0.45            # NMS IoU threshold

# ─── COCO Class IDs → Our vehicle categories ─────────────────────────────────
# Only these COCO classes are kept; all others are ignored.
COCO_VEHICLE_CLASSES = {
    1:  "bike",    # bicycle
    2:  "car",
    3:  "bike",    # motorcycle → merged with bicycle under "bike"
    5:  "bus",
    7:  "truck",
}

# Display label (what shows on the bounding box)
DISPLAY_LABELS = {
    "car":   "Car",
    "bike":  "Bike",
    "bus":   "Bus",
    "truck": "Truck",
}

# Bounding-box colours per class (BGR for OpenCV)
CLASS_COLORS = {
    "car":   (0,   255, 100),   # green
    "bike":  (255, 200,  0),    # cyan-yellow
    "bus":   (0,   100, 255),   # orange
    "truck": (180,  0,  255),   # purple
}

# ─── Counting Line ────────────────────────────────────────────────────────────
# Expressed as a fraction of frame height (0.0 = top, 1.0 = bottom).
# Vehicles whose centroid crosses this horizontal line are counted.
COUNTING_LINE_RATIO = 0.55      # line drawn at 55 % of frame height
COUNTING_LINE_COLOR = (0, 0, 255)   # red
COUNTING_LINE_THICKNESS = 2

# ─── Traffic Density Thresholds ───────────────────────────────────────────────
# Based on total vehicles visible in frame at any given moment.
DENSITY_THRESHOLDS = {
    "LOW":      (0,  5),
    "MEDIUM":   (6,  12),
    "HIGH":     (13, 20),
    "CRITICAL": (21, float("inf")),
}

# Weight given to frame-coverage ratio vs raw count (0–1)
COVERAGE_WEIGHT = 0.4   # 40 % coverage, 60 % count

# ─── SORT Tracker ─────────────────────────────────────────────────────────────
SORT_MAX_AGE    = 10    # frames to keep a lost track alive
SORT_MIN_HITS   = 2     # minimum detections before track is confirmed
SORT_IOU_THRESH = 0.30  # IoU threshold for track association

# ─── Output ───────────────────────────────────────────────────────────────────
EVENT_EMIT_INTERVAL_SEC = 1.0   # emit a TrafficEvent JSON every N seconds of video
SHOW_FPS   = True
SHOW_HUD   = True               # vehicle counts + density overlay
FONT_SCALE = 0.65
FONT_THICKNESS = 2
