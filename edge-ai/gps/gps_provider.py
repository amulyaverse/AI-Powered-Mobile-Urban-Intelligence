import csv
import bisect
from typing import Dict, Optional, Tuple

class GPSProvider:
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.points = []
        self._load_csv()

    def _load_csv(self):
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = float(row['timestamp'])
                lat = float(row['latitude'])
                lon = float(row['longitude'])
                self.points.append({
                    'timestamp': timestamp,
                    'lat': lat,
                    'lon': lon
                })
        # Ensure points are sorted by timestamp
        self.points.sort(key=lambda x: x['timestamp'])

    def get_current_position(self, time_sec: float) -> Optional[Dict[str, float]]:
        """
        Get the interpolated GPS position at a given timestamp (seconds).
        Returns {'latitude': lat, 'longitude': lon, 'timestamp': time_sec}
        """
        if not self.points:
            return None

        timestamps = [p['timestamp'] for p in self.points]
        
        # If time is before the first point, return the first point
        if time_sec <= timestamps[0]:
            return {
                'latitude': self.points[0]['lat'],
                'longitude': self.points[0]['lon'],
                'timestamp': time_sec
            }
            
        # If time is after the last point, return the last point
        if time_sec >= timestamps[-1]:
            return {
                'latitude': self.points[-1]['lat'],
                'longitude': self.points[-1]['lon'],
                'timestamp': time_sec
            }

        # Find where time_sec fits in the timestamps list
        idx = bisect.bisect_right(timestamps, time_sec)
        p1 = self.points[idx - 1]
        p2 = self.points[idx]

        # Linear interpolation
        t1, t2 = p1['timestamp'], p2['timestamp']
        ratio = (time_sec - t1) / (t2 - t1) if t2 > t1 else 0

        lat = p1['lat'] + ratio * (p2['lat'] - p1['lat'])
        lon = p1['lon'] + ratio * (p2['lon'] - p1['lon'])

        return {
            'latitude': lat,
            'longitude': lon,
            'timestamp': time_sec
        }

if __name__ == "__main__":
    import os
    # Simple test
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'routes', 'BUS_021_demo.csv')
    if os.path.exists(csv_path):
        provider = GPSProvider(csv_path)
        print("At 0s:", provider.get_current_position(0))
        print("At 1s:", provider.get_current_position(1))
        print("At 18s:", provider.get_current_position(18))
    else:
        print(f"Test CSV not found at {csv_path}")
