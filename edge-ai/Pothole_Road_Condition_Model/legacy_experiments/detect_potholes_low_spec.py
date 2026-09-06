import cv2
import argparse
import torch
from ultralytics import YOLO

# Temporary patch for PyTorch 2.6+ compatibility with older YOLOv8 checkpoints
# This disables the strict weights_only check that causes unpickling errors.
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

def main(weights_path, source, output_path=None, imgsz=320, skip_frames=2, conf_thresh=0.25):
    # Load the pre-trained YOLOv8 model for pothole detection
    print(f"Loading YOLOv8 model from {weights_path}...")
    model = YOLO(weights_path)
    
    # Check if GPU is actually available and supported by PyTorch
    if torch.cuda.is_available():
        print(f"CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
        device = 'cuda'
    else:
        print("CUDA not available or GPU too old for PyTorch. Falling back to CPU...")
        device = 'cpu'

    # Create a custom tracker configuration file so the tracker actually assigns IDs
    # to low-confidence detections. By default, the tracker ignores anything under ~0.5 conf.
    import yaml
    custom_tracker_path = "custom_tracker.yaml"
    tracker_config = {
        'tracker_type': 'bytetrack',
        'track_high_thresh': max(0.1, conf_thresh - 0.05), # Allow tracking to start at lower confidences
        'track_low_thresh': 0.05,
        'new_track_thresh': max(0.1, conf_thresh - 0.05),
        'track_buffer': 30,
        'match_thresh': 0.8
    }
    with open(custom_tracker_path, 'w') as f:
        yaml.dump(tracker_config, f)

    # Initialize video capture (0 for default webcam, or path to video file)
    try:
        source_idx = int(source)
        cap = cv2.VideoCapture(source_idx)
        print(f"Opening live camera feed (ID: {source_idx})...")
    except ValueError:
        cap = cv2.VideoCapture(source)
        print(f"Opening video file {source}...")

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    # Set up video writer if output path is provided
    video_writer = None
    if output_path:
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:  # Fallback for some webcams
            fps = 30
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    # Keep track of unique potholes using their tracking IDs
    unique_potholes = set()

    print(f"Starting inference at {imgsz}x{imgsz} resolution with conf={conf_thresh}... Press 'q' to quit.")
    
    frame_count = 0
    annotated_frame = None
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream or error.")
            break
            
        frame_count += 1
        
        # Only run the heavy YOLO tracking every N frames to keep the window responsive on slow CPUs
        if frame_count % skip_frames == 0 or annotated_frame is None:
            # Run YOLOv8 object tracking on the frame
            # We use the custom tracker config so it tracks low-confidence objects
            results = model.track(
                frame, 
                persist=True, 
                conf=conf_thresh, 
                verbose=False, 
                imgsz=imgsz, 
                device=device,
                tracker=custom_tracker_path
            )

            # Process results for the current frame
            if results[0].boxes is not None and results[0].boxes.id is not None:
                # Extract tracking IDs and add them to our set of unique potholes
                boxes = results[0].boxes.xyxy.cpu()
                track_ids = results[0].boxes.id.int().cpu().tolist()
                confidences = results[0].boxes.conf.cpu().tolist()

                for track_id, conf in zip(track_ids, confidences):
                    if conf >= conf_thresh: # Double check confidence
                        unique_potholes.add(track_id)

            # Draw the bounding boxes and IDs on the frame
            annotated_frame = results[0].plot()

            # Add text overlay for total potholes detected
            cv2.putText(
                annotated_frame, 
                f'Total Unique Potholes: {len(unique_potholes)}', 
                (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 255, 0), # Green color
                2, 
                cv2.LINE_AA
            )

            # Add text overlay for currently visible potholes
            visible_potholes = len(results[0].boxes) if results[0].boxes is not None else 0
            cv2.putText(
                annotated_frame, 
                f'Visible Now: {visible_potholes}', 
                (20, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 165, 255), # Orange color
                2, 
                cv2.LINE_AA
            )

        # Show the annotated frame (either freshly processed or from the previous frame)
        cv2.imshow("Pothole Detection - YOLOv8 (Low Spec Optimized)", annotated_frame)

        # Write to output video if specified
        if video_writer:
            video_writer.write(annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()
    
    print("-" * 30)
    print(f"Total Unique Potholes Detected: {len(unique_potholes)}")
    print("-" * 30)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Pothole Detection and Tracking using YOLOv8 (Low Spec)")
    parser.add_argument('--weights', type=str, default='yolov8n.pt', help='Path to YOLOv8 weights file (e.g., best.pt)')
    parser.add_argument('--source', type=str, default='0', help='Video source: 0 for webcam, or path to video file')
    parser.add_argument('--output', type=str, default=None, help='Path to save output video (e.g., output.mp4)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold for detection (e.g., 0.10)')
    
    args = parser.parse_args()
    main(args.weights, args.source, args.output, conf_thresh=args.conf)

# python detect_potholes_low_spec.py --weights best.pt --source 0 --conf 0.10