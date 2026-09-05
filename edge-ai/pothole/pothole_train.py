from ultralytics import YOLO
import os
import torch

# Temporary patch for PyTorch 2.6+ compatibility with older YOLOv8 checkpoints
# We safely grab the true original load function directly from the serialization module
# so that even if the notebook cell is run 100 times, it never loops.
_true_original_load = torch.serialization.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _true_original_load(*args, **kwargs)

torch.load = safe_load
torch.serialization.load = safe_load

def main():
    # Load the base YOLOv8 nano model (yolov8n.pt)
    # Nano is recommended for faster training, especially on low-spec hardware.
    model = YOLO("yolov8n.pt")

    # Path to the data.yaml of the downloaded Roboflow dataset
    # IMPORTANT FOR COLAB: You must change this to your Colab path (e.g., '/content/pothole-indian-road-5/data.yaml')
    data_yaml_path = r"E:\Application Dev\VS Code files\Git\pothole-indian-road-5\data.yaml"

    print(f"Starting training using dataset: {data_yaml_path}")
    
    # Check if GPU is available (crucial for Colab)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Start training
    # epochs=50 is a good starting point, but you can increase it for better accuracy.
    # imgsz=640 is standard. Lower it (e.g., to 320 or 416) if you run out of memory.
    results = model.train(
        data=data_yaml_path,
        epochs=50,
        imgsz=640,
        batch=16, # Increased batch size since Colab GPUs have more memory
        device=device, 
        name='pothole_model'
    )

    print("Training complete!")
    print(f"Your best weights are saved in: {os.path.abspath('runs/detect/pothole_model/weights/best.pt')}")

if __name__ == '__main__':
    # Fix for multiprocessing in Windows
    import multiprocessing
    multiprocessing.freeze_support()
    main()