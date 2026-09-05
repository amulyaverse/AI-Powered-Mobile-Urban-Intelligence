from ultralytics import YOLO
import os
import torch

# Fix for PyTorch compatibility with some YOLO weights
_original_load = torch.load
def safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = safe_load

def main():
    print("Initializing YOLOv8 Nano model...")
    # Load the base YOLOv8 nano model
    model = YOLO("yolov8n.pt")

    # Path to the already downloaded dataset
    data_yaml_path = r"E:\Application Dev\VS Code files\Git\pothole-indian-road-5\data.yaml"

    print(f"Starting training using dataset: {data_yaml_path}")
    
    # Start training
    # Adjust epochs and batch size based on your hardware capabilities.
    # Using device='cpu' as a safe default, change to 'cuda' or 0 if you have an NVIDIA GPU.
    results = model.train(
        data=data_yaml_path,
        epochs=30,      # A good starting point for a prototype
        imgsz=640,
        batch=4,        
        device='cpu',   # Change to '0' if using a dedicated GPU
        project="pothole_training_runs",
        name="pothole_model_v1"
    )

    print("Training complete!")
    print("Your best weights will be saved in: pothole_training_runs/pothole_model_v1/weights/best.pt")

if __name__ == '__main__':
    # Fix for multiprocessing in Windows
    import multiprocessing
    multiprocessing.freeze_support()
    main()

