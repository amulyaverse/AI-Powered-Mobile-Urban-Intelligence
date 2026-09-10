import argparse
import time
import requests
import json
import logging
from gps_provider import GPSProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

API_BASE_URL = "http://localhost:8000/api"

def main():
    parser = argparse.ArgumentParser(description="GPS Replay Engine")
    parser.add_argument("--bus", type=str, required=True, help="Bus ID (e.g., BUS_021)")
    parser.add_argument("--file", type=str, required=True, help="Path to CSV route file")
    parser.add_argument("--speed", type=float, default=1.0, help="Replay speed multiplier")
    parser.add_argument("--loop", action="store_true", help="Loop the replay continuously")
    parser.add_argument("--update_interval", type=float, default=2.0, help="How often to send GPS updates (in real seconds)")
    
    args = parser.parse_args()

    provider = GPSProvider(args.file)
    if not provider.points:
        logging.error("No points found in the CSV file.")
        return

    max_timestamp = provider.points[-1]['timestamp']
    logging.info(f"Loaded {len(provider.points)} points. Route duration: {max_timestamp} seconds.")
    
    # Store the state locally so the edge AI script can read it.
    # A simple way to do this is to write the current state to a JSON file.
    state_file = f"{args.bus}_current_state.json"

    while True:
        start_time_real = time.time()
        current_time_sim = 0.0
        
        logging.info(f"Starting replay for {args.bus} at {args.speed}x speed.")
        
        while current_time_sim <= max_timestamp:
            # 1. Get current position
            pos = provider.get_current_position(current_time_sim)
            
            if pos:
                # 2. Update local state file for YOLO script to read (if they are separate processes)
                state = {
                    "bus_id": args.bus,
                    "latitude": pos["latitude"],
                    "longitude": pos["longitude"],
                    "timestamp": pos["timestamp"],
                    "speed": args.speed
                }
                with open(state_file, "w") as f:
                    json.dump(state, f)
                
                # 3. Send update to backend
                url = f"{API_BASE_URL}/buses/{args.bus}/location"
                payload = {
                    "latitude": pos["latitude"],
                    "longitude": pos["longitude"],
                    "timestamp": pos["timestamp"], # Using sim timestamp, or you could use real time
                    "status": "active"
                }
                
                try:
                    response = requests.post(url, json=payload, timeout=2)
                    if response.status_code in [200, 201]:
                        logging.info(f"Updated GPS: {pos['latitude']:.6f}, {pos['longitude']:.6f} at sim time {pos['timestamp']:.1f}s")
                    else:
                        logging.warning(f"Failed to update GPS. Status: {response.status_code}")
                except Exception as e:
                    logging.warning(f"Could not connect to backend: {e}")
            
            # Wait until next update
            time.sleep(args.update_interval)
            
            # Advance simulation time based on real time elapsed
            elapsed_real = time.time() - start_time_real
            current_time_sim = elapsed_real * args.speed
            
        logging.info("Reached end of route.")
        if not args.loop:
            break
        logging.info("Looping back to start.")

if __name__ == "__main__":
    main()
