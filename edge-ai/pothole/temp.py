# By Antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("road-damage-detection-ds22n").project("road-damage-dataset-8jvz5")
version = project.version(2)
dataset = version.download("yolov8")
                
# By Antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("intel-unnati-training-program").project("pothole-detection-bqu6s")
version = project.version(9)
dataset = version.download("yolov8")
                
# By Antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("indian-institute-of-technology-madras-xamot").project("pothole-detection-huf2x")
version = project.version(2)
dataset = version.download("yolov8")
                
# By antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("dopeai").project("road-condition-dope-ai-wyljz")
version = project.version(2)
dataset = version.download("yolov8")
                
# By antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("health-care-lab-rquk6").project("road-potholes-and-cracks")
version = project.version(1)
dataset = version.download("yolov8")                

# By antigravity
from roboflow import Roboflow
rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
project = rf.workspace("new-workspace-kj87b").project("road-damage-detection-iicdh")
version = project.version(10)
dataset = version.download("yolov8")
                

# from roboflow import Roboflow
# rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
# project = rf.workspace("unikom-unpam-bersatu").project("pothole-detection-woo5m")
# version = project.version(1)
# dataset = version.download("yolov8")
                

# from roboflow import Roboflow
# rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
# project = rf.workspace("aegis").project("pothole-detection-i00zy")
# version = project.version(2)
# dataset = version.download("yolov8")
                

# from roboflow import Roboflow
# rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
# project = rf.workspace("brad-dwyer").project("pothole-voxrl")
# version = project.version(1)
# dataset = version.download("yolov8")
                
# from roboflow import Roboflow
# rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
# project = rf.workspace("project-o3ot9").project("indian-road-potholes")
# version = project.version(5)
# dataset = version.download("yolov8")

# from roboflow import Roboflow
# rf = Roboflow(api_key="wr8L9ESEMlmrTRHJb8w7")
# project = rf.workspace("yeeun-kim-fyvoj").project("pothole-vhmow")
# version = project.version(18)
# dataset = version.download("yolov8")

# from ultralytics import YOLO
# import os
# import torch

# # Temporary patch for PyTorch 2.6+ compatibility with older YOLOv8 checkpoints
# # This disables the strict weights_only check that causes unpickling errors.
# _original_load = torch.load
# def safe_load(*args, **kwargs):
#     kwargs['weights_only'] = False
#     return _original_load(*args, **kwargs)
# torch.load = safe_load

# def main():
#     # Load the base YOLOv8 nano model (yolov8n.pt)
#     # Nano is recommended for faster training, especially on low-spec hardware.
#     model = YOLO("yolov8n.pt")

#     # Path to the data.yaml of the downloaded Roboflow dataset
#     # Using 'pothole-indian-road-5' as it has proper train/test/valid folders.
#     data_yaml_path = r"E:\Application Dev\VS Code files\Git\pothole-indian-road-5\data.yaml"

#     print(f"Starting training using dataset: {data_yaml_path}")
    
#     # Start training
#     # epochs=50 is a good starting point, but you can increase it for better accuracy.
#     # imgsz=640 is standard. Lower it (e.g., to 320 or 416) if you run out of memory.
#     # batch=4 is set low to prevent memory issues on lower-spec machines.
#     # device='cpu' forces it to use CPU (since older NVIDIA GPUs aren't supported). 
#     # Remove `device='cpu'` if you move this script to a machine with a newer NVIDIA GPU.
#     results = model.train(
#         data=data_yaml_path,
#         epochs=50,
#         imgsz=640,
#         batch=4,
#         device='cpu', 
#         name='pothole_model'
#     )

#     print("Training complete!")
#     print(f"Your best weights are saved in: {os.path.abspath('runs/detect/pothole_model/weights/best.pt')}")

# if __name__ == '__main__':
#     # Fix for multiprocessing in Windows
#     import multiprocessing
#     multiprocessing.freeze_support()
#     main()