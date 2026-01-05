"""
EasiVisi - Configuration Management
"""
import os

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
RUNS_DIR = os.path.join(BASE_DIR, 'runs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Ensure directories exist
for dir_path in [DATASET_DIR, RUNS_DIR, MODELS_DIR, UPLOAD_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Flask configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'easivisi-dev-key-change-in-prod')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    ALLOWED_MODEL_EXTENSIONS = {'pt', 'onnx', 'engine', 'tflite', 'torchscript', 'mlpackage'}
    
    # Dataset paths
    DATASET_DIR = DATASET_DIR
    RUNS_DIR = RUNS_DIR
    MODELS_DIR = MODELS_DIR
    UPLOAD_DIR = UPLOAD_DIR
    
    # Training defaults
    DEFAULT_MODEL = 'yolov8n.pt'
    DEFAULT_EPOCHS = 50
    DEFAULT_BATCH_SIZE = 16
    DEFAULT_IMG_SIZE = 640
    DEFAULT_DEVICE = 'cpu'
    
    # Export defaults
    DEFAULT_EXPORT_IMGSZ = 640
    DEFAULT_EXPORT_OPSET = 17
    
    # Available YOLO models
    YOLO_MODELS = {
        'yolov8n.pt': {'name': 'YOLOv8 Nano', 'size': 'Small', 'speed': 'Fastest'},
        'yolov8s.pt': {'name': 'YOLOv8 Small', 'size': 'Medium', 'speed': 'Fast'},
        'yolov8m.pt': {'name': 'YOLOv8 Medium', 'size': 'Large', 'speed': 'Balanced'},
        'yolov8l.pt': {'name': 'YOLOv8 Large', 'size': 'XLarge', 'speed': 'Slower'},
        'yolov8x.pt': {'name': 'YOLOv8 Extra Large', 'size': 'XXLarge', 'speed': 'Slowest'},
    }

def get_config():
    return Config()
