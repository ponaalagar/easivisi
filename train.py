from ultralytics import YOLO
import os

ROOT_DIR = "dataset\\new" #path to the root directory contains the dataset 
DATA_YAML = os.path.join(r"dataset\\new\\dataset.yaml") #path to the dataset.yaml file

def main():
    model = YOLO("yolov8n.pt")  # or yolov8s.pt etc.

    results = model.train(
        data=DATA_YAML,
        epochs=50,
        imgsz=640,
        batch=16,
        workers=4,
        device= 0,              # 'cpu' if no GPU
        project="runs_stain",
        name="yolov8_stain_v1",
        pretrained=True,
    )

    print("Training finished.")
    print("Run directory:", results.save_dir)


if __name__ == "__main__":
    main()
