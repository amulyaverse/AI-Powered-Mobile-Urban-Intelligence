from __future__ import annotations
import time
import math
import cv2
from pothole_config import (
    DEFAULT_MODEL, CONFIDENCE_THRESHOLD, DISTANCE_THRESHOLD, 
    EVENT_EMIT_INTERVAL_SEC, GPS_DISTANCE_THRESHOLD,
    HEALING_DISTANCE_RADIUS_METERS, HEALING_FRAME_CONFIDENCE,
    DEDUPLICATION_RADIUS_METERS
)
from pothole_detector import PotholeDetector
from pothole_severity import cluster_boxes, determine_severity_cluster
import uuid

from datetime import datetime, timezone

def validate_gps(lat, lon):
    if lat is None or lon is None:
        raise ValueError("GPS coordinates cannot be None")
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid GPS coordinates: {lat}, {lon}")
    if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        raise ValueError(f"GPS coordinates cannot be NaN or Inf: {lat}, {lon}")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude out of bounds: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude out of bounds: {lon}")
    return lat, lon

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class HealingManager:
    def __init__(self, known_potholes_list, radius_meters=15, frame_confidence=15, deduplication_radius=2.0):
        self.radius_meters = radius_meters
        self.frame_confidence = frame_confidence
        self.deduplication_radius = deduplication_radius
        self.known_potholes = {}
        self.empty_frame_counts = {}
        
        for p in known_potholes_list:
            pid = p.get("event_id") or p.get("id") or str(uuid.uuid4())
            if pid in self.known_potholes:
                raise ValueError(f"Duplicate pothole ID found: {pid}")
            try:
                lat, lon = validate_gps(p.get("latitude"), p.get("longitude"))
            except ValueError:
                continue
            self.known_potholes[pid] = {"latitude": lat, "longitude": lon}
            self.empty_frame_counts[pid] = 0
            
    def get_or_add_pothole(self, lat, lon):
        lat, lon = validate_gps(lat, lon)
        
        for pid, p in self.known_potholes.items():
            if haversine(lat, lon, p["latitude"], p["longitude"]) <= self.deduplication_radius:
                return pid # Already known nearby
        pid = str(uuid.uuid4())
        self.known_potholes[pid] = {"latitude": lat, "longitude": lon}
        self.empty_frame_counts[pid] = 0
        return pid
        
    def process_frame(self, current_lat, current_lon, potholes_detected):
        current_lat, current_lon = validate_gps(current_lat, current_lon)
        resolved_potholes = []
        if potholes_detected:
            for pid, p in self.known_potholes.items():
                if haversine(current_lat, current_lon, p["latitude"], p["longitude"]) <= self.radius_meters:
                    self.empty_frame_counts[pid] = 0
        else:
            for pid, p in self.known_potholes.items():
                if haversine(current_lat, current_lon, p["latitude"], p["longitude"]) <= self.radius_meters:
                    self.empty_frame_counts[pid] += 1
                    if self.empty_frame_counts[pid] >= self.frame_confidence:
                        resolved_potholes.append((pid, p))
                        
        for pid, p in resolved_potholes:
            del self.known_potholes[pid]
            del self.empty_frame_counts[pid]
            yield pid, p
            
    def get_cache_list(self):
        return [{"event_id": pid, "latitude": p["latitude"], "longitude": p["longitude"]} for pid, p in self.known_potholes.items()]

import sys
import os

class VideoSyncedGPSGenerator:
    """
    GPS Generator that yields coordinates from a CSV based on video timestamp.
    """
    def __init__(self, csv_file=None):
        if csv_file is None:
            # Default to the demo CSV if not provided
            base_dir = os.path.dirname(os.path.abspath(__file__))
            csv_file = os.path.join(base_dir, '..', '..', 'gps', 'routes', 'BUS_021_demo.csv')
            
        gps_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gps')
        if gps_dir not in sys.path:
            sys.path.insert(0, gps_dir)
            
        try:
            from gps_provider import GPSProvider
            self.provider = GPSProvider(csv_file)
        except ImportError:
            print("Warning: GPSProvider not found, falling back to 0,0")
            self.provider = None
        
    def get_coordinates(self, video_time_sec):
        if self.provider:
            pos = self.provider.get_current_position(video_time_sec)
            if pos:
                return pos['latitude'], pos['longitude']
        return 28.6139, 77.2090

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

class PotholePipeline:
    def __init__(
        self,
        source: str | int = 0,
        model_name: str = DEFAULT_MODEL,
        conf: float = CONFIDENCE_THRESHOLD,
        show: bool = False,
        bus_id: str = "BUS_01",
        camera_id: str = "CAM_FRONT",
        known_potholes: list = None
    ):
        self.source = source
        self.show = show
        self.bus_id = bus_id
        self.camera_id = camera_id
        
        self.detector = PotholeDetector(model_path=model_name, conf=conf)
        self.gps_gen = VideoSyncedGPSGenerator()
        self.healing_manager = HealingManager(
            known_potholes_list=known_potholes or [],
            radius_meters=HEALING_DISTANCE_RADIUS_METERS,
            frame_confidence=HEALING_FRAME_CONFIDENCE,
            deduplication_radius=DEDUPLICATION_RADIUS_METERS
        )

    def run(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open source: {self.source}")
            
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_area = frame_width * frame_height
        
        last_log_time = 0.0
        last_log_lat, last_log_lon = 0.0, 0.0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0 or math.isnan(fps):
                    fps = 30.0
                
                frame_count = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                video_time_sec = frame_count / fps
                    
                current_time = time.time()
                current_lat, current_lon = self.gps_gen.get_coordinates(video_time_sec)
                
                try:
                    current_lat, current_lon = validate_gps(current_lat, current_lon)
                except ValueError as e:
                    print(f"[Pipeline] Invalid GPS: {e}")
                    continue
                
                raw_boxes = self.detector.detect(frame)
                clusters = cluster_boxes(raw_boxes, distance_threshold=DISTANCE_THRESHOLD)
                
                highest_severity_in_frame = None
                best_event_to_log = None
                
                time_elapsed = (current_time - last_log_time) >= EVENT_EMIT_INTERVAL_SEC
                dist_elapsed = calculate_distance(current_lat, current_lon, last_log_lat, last_log_lon) >= GPS_DISTANCE_THRESHOLD
                should_log_this_frame = time_elapsed and dist_elapsed
                
                # Check for healing
                potholes_detected = len(clusters) > 0
                for resolved_pid, resolved_pothole in self.healing_manager.process_frame(current_lat, current_lon, potholes_detected):
                    yield {
                        "event_id": resolved_pid,
                        "event_type": "Pothole_Resolved",
                        "bus_id": self.bus_id,
                        "camera_id": self.camera_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "latitude": resolved_pothole["latitude"],
                        "longitude": resolved_pothole["longitude"],
                        "action": "DELETE"
                    }
                
                for cluster in clusters:
                    w = cluster['x2'] - cluster['x1']
                    h = cluster['y2'] - cluster['y1']
                    cluster_area = w * h
                    
                    severity = determine_severity_cluster(w, cluster_area, frame_width, frame_area, cluster['count'])
                    
                    if self.show:
                        label = f"Cluster ({cluster['count']}x) | S: {severity}"
                        color = (0, 255, 0) # Green for Low
                        if severity == "MEDIUM": color = (0, 255, 255) # Yellow
                        elif severity == "HIGH": color = (0, 165, 255) # Orange
                        elif severity == "VERY HIGH": color = (0, 0, 255) # Red
                        
                        cv2.rectangle(frame, (cluster['x1'], cluster['y1']), (cluster['x2'], cluster['y2']), color, 2)
                        cv2.putText(frame, label, (cluster['x1'], max(0, cluster['y1'] - 10)), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                                    
                    # Only yield events that are "MEDIUM", "HIGH", or "VERY HIGH" severity
                    if severity in ["MEDIUM", "HIGH", "VERY HIGH"]:
                        event_data = {
                            "event_type": f"{cluster['class_name']}_cluster" if cluster['count'] > 1 else cluster['class_name'],
                            "confidence": round(cluster['conf'], 2),
                            "severity": severity,
                            "bus_id": self.bus_id,
                            "camera_id": self.camera_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "latitude": current_lat,
                            "longitude": current_lon
                        }
                        
                        # Rank severities to pick the worst one
                        severities = ["LOW", "MEDIUM", "HIGH", "VERY HIGH"]
                        if highest_severity_in_frame is None or severities.index(severity) > severities.index(highest_severity_in_frame):
                            highest_severity_in_frame = severity
                            best_event_to_log = event_data
                            
                if self.show:
                    cv2.imshow("Pothole Detection Pipeline", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("[Pipeline] User quit.")
                        break
                        
                # Yield and update rate limiting if criteria is met
                if should_log_this_frame and best_event_to_log is not None:
                    last_log_time = current_time
                    last_log_lat, last_log_lon = current_lat, current_lon
                    # Add to local cache so we know it's there
                    pid = self.healing_manager.get_or_add_pothole(current_lat, current_lon)
                    best_event_to_log["event_id"] = pid
                    yield best_event_to_log
                    
        finally:
            cap.release()
            if self.show:
                cv2.destroyAllWindows()

