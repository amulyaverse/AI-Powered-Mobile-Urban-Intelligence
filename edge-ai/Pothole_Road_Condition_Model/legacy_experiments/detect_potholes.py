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

def main(weights_path, source, output_path=None):
    # Load the pre-trained YOLOv8 model for pothole detection
    print(f"Loading YOLOv8 model from {weights_path}...")
    model = YOLO(weights_path)

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

    print("Starting inference... Press 'q' to quit.")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("End of video stream or error.")
            break

        # Run YOLOv8 object tracking on the frame
        # persist=True keeps tracking IDs consistent across frames
        results = model.track(frame, persist=True, conf=0.25, verbose=False)

        # Process results for the current frame
        if results[0].boxes is not None and results[0].boxes.id is not None:
            # Extract tracking IDs and add them to our set of unique potholes
            boxes = results[0].boxes.xyxy.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            confidences = results[0].boxes.conf.cpu().tolist()

            for track_id, conf in zip(track_ids, confidences):
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

        # Show the annotated frame
        cv2.imshow("Pothole Detection - YOLOv8", annotated_frame)

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
    parser = argparse.ArgumentParser(description="Pothole Detection and Tracking using YOLOv8")
    parser.add_argument('--weights', type=str, default='yolov8n.pt', help='Path to YOLOv8 weights file (e.g., best.pt)')
    parser.add_argument('--source', type=str, default='0', help='Video source: 0 for webcam, or path to video file (e.g., video.mp4)')
    parser.add_argument('--output', type=str, default=None, help='Path to save output video (e.g., output.mp4)')
    
    args = parser.parse_args()
    main(args.weights, args.source, args.output)
