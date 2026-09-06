from __future__ import annotations
import argparse
import json
import os
import sys
from pothole_pipeline import PotholePipeline

def resolve_weights_path(weights_arg):
    # If it's a direct valid path or yolov8n.pt (which ultralytics handles by downloading)
    if os.path.exists(weights_arg) or weights_arg == "yolov8n.pt":
        return weights_arg
        
    # Check the specific local custom weights directory
    custom_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "edge_inference")
    custom_path = os.path.join(custom_dir, weights_arg)
    if os.path.exists(custom_path):
        return custom_path
        
    print(f"Warning: Could not find weights at {weights_arg} or {custom_path}. Passing to YOLO anyway.")
    return weights_arg

def main():
    parser = argparse.ArgumentParser(description="AI-Powered Mobile Urban Intelligence - Pothole Module")
    parser.add_argument("--source", type=str, required=True, help="Video source file or camera index")
    parser.add_argument("--weights", type=str, default="yolov8n.pt", help="Path to YOLO weights")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--show", action="store_true", help="Display OpenCV preview window")
    parser.add_argument("--output-log", type=str, default="pothole_events.jsonl", help="Output JSONL log file")
    parser.add_argument("--known-potholes", type=str, default="known_potholes.json", help="Path to local pothole cache JSON")
    
    args = parser.parse_args()
    
    # Resolve the video source
    source = args.source
    if source.isdigit():
        source = int(source)
    elif not os.path.exists(source):
        # Fallback check for the user's specific directory
        custom_src_dir = os.path.dirname(os.path.abspath(__file__))
        custom_src = os.path.join(custom_src_dir, source)
        if os.path.exists(custom_src):
            source = custom_src
        else:
            print(f"Error: Source video {source} not found.")
            sys.exit(1)
            
    # Resolve the weights
    weights_path = resolve_weights_path(args.weights)
    
    # Load known potholes cache if it exists
    known_potholes = []
    if os.path.exists(args.known_potholes):
        with open(args.known_potholes, 'r') as f:
            try:
                known_potholes = json.load(f)
                
                # Protect against duplicate IDs
                seen_ids = set()
                for p in known_potholes:
                    pid = p.get("event_id") or p.get("id")
                    if pid:
                        if pid in seen_ids:
                            print(f"Error: Duplicate ID {pid} found in {args.known_potholes}. Aborting to protect data.")
                            sys.exit(1)
                        seen_ids.add(pid)
                        
                print(f"[CLI] Loaded {len(known_potholes)} known potholes from cache.")
            except json.JSONDecodeError as e:
                print(f"Error parsing {args.known_potholes}: {e}. Aborting to protect data.")
                sys.exit(1)
            except Exception as e:
                print(f"Error loading {args.known_potholes}: {e}. Aborting to protect data.")
                sys.exit(1)
                
    print(f"[CLI] Starting pipeline...")
    print(f"[CLI] Source: {source}")
    print(f"[CLI] Weights: {weights_path}")
    print(f"[CLI] Output Log: {args.output_log}")
    
    pipeline = PotholePipeline(
        source=source,
        model_name=weights_path,
        conf=args.conf,
        show=args.show,
        known_potholes=known_potholes
    )
    
    try:
        with open(args.output_log, 'a') as f:
            for event in pipeline.run():
                event_json = json.dumps(event)
                print(f"[Event] {event_json}")
                f.write(event_json + "\n")
                f.flush()
    finally:
        # Save the updated known potholes cache back to the file
        updated_cache = pipeline.healing_manager.get_cache_list()
        tmp_path = args.known_potholes + ".tmp"
        with open(tmp_path, 'w') as f:
            json.dump(updated_cache, f, indent=4)
        os.replace(tmp_path, args.known_potholes)
        print(f"[CLI] Saved {len(updated_cache)} known potholes to cache.")
            
if __name__ == "__main__":
    main()

