import os
from roboflow import Roboflow
from ultralytics import YOLO

def main():
    print("Step 1: Downloading Dataset from Roboflow...")
    # Using the Roboflow snippet from your temp.py
    # Make sure you keep your API key secure if pushing to a public github!
    rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7") 
    project = rf.workspace("project-o3ot9").project("indian-road-potholes")
    version = project.version(5)
    dataset = version.download("yolov8")
    
    print("\nStep 2: Initializing YOLOv8 Nano model...")
    # Load the base YOLOv8 nano model
    model = YOLO("yolov8n.pt")

    # The dataset.location contains the path to the downloaded dataset
    data_yaml_path = os.path.join(dataset.location, "data.yaml")
    print(f"\nStarting training using dataset: {data_yaml_path}")
    
    # Step 3: Start training with High-End settings (GPU, High Batch, More Epochs)
    results = model.train(
        data=data_yaml_path,
        epochs=100,      # Train longer for better accuracy
        imgsz=640,       # Standard image size
        batch=16,        # Higher batch size takes advantage of Cloud GPU VRAM (can push to 32 or 64 if GPU is good)
        device=0,        # Specifically tells ultralytics to use CUDA GPU 0
        project="kaggle_pothole_training",
        name="pothole_model_cloud",
        patience=20      # Early stopping if no improvement for 20 epochs
    )

    print("\nTraining complete!")
    print("You can find your weights in: kaggle_pothole_training/pothole_model_cloud/weights/best.pt")
    print("Download 'best.pt' and move it to your edge device for inference.")

if __name__ == '__main__':
    main()

