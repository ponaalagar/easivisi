# EasiVisi - Visual AI Training Platform 🎯

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-green.svg)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple.svg)](https://ultralytics.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Train custom object detection models without writing a single line of code!**

EasiVisi is a powerful, user-friendly **Flask web application** that enables users to **annotate images**, **train**, and **fine-tune YOLO models** for custom object detection tasks — all through an intuitive browser-based interface. No deep learning expertise required!

---

## 🌟 Key Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Web-Based Image Annotation** | Draw bounding boxes directly in your browser with an intuitive annotation tool |
| 🚀 **One-Click YOLO Training** | Train YOLOv8 models with customizable hyperparameters via simple UI controls |
| 🔧 **Model Fine-Tuning** | Fine-tune pre-trained YOLO models on your custom datasets |
| 📊 **Real-Time Training Metrics** | Monitor loss, mAP, and other metrics with TensorBoard integration |
| 💾 **Dataset Management** | Organize, import, and export datasets in YOLO format |
| 🎯 **Object Detection Inference** | Test trained models on new images instantly |
| 📱 **Responsive Design** | Works seamlessly on desktop and tablet devices |

---

## 🎯 Use Cases

- **Manufacturing Quality Control** — Detect defects, stains, or anomalies in products
- **Retail & Inventory** — Count and classify items on shelves
- **Agriculture** — Identify crop diseases, pests, or ripe produce
- **Security & Surveillance** — Custom object detection for monitoring systems
- **Medical Imaging** — Train models for preliminary screening (non-diagnostic)
- **Sports Analytics** — Track players, equipment, and movements
- **Wildlife Conservation** — Monitor and count animal species

---

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python, Flask |
| **Deep Learning** | PyTorch, Ultralytics YOLOv8 |
| **Image Processing** | OpenCV, Pillow, NumPy |
| **Visualization** | Matplotlib, Seaborn, TensorBoard |
| **Dataset Tools** | PyYAML, Pandas, pycocotools |
| **Frontend** | HTML5, CSS3, JavaScript |

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) NVIDIA GPU with CUDA for faster training

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ponaalagar/easivisi.git
cd easivisi

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage

### 1. Prepare Your Dataset

Organize your images and annotations in the YOLO format:

```
dataset/
├── images/
│   ├── train/
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   └── ...
│   └── val/
│       ├── image1.jpg
│       └── ...
├── labels/
│   ├── train/
│   │   ├── image1.txt
│   │   └── ...
│   └── val/
│       └── ...
└── dataset.yaml
```

### 2. Configure Dataset YAML

Create a `dataset.yaml` file:

```yaml
path: ./dataset  # dataset root directory
train: images/train  # training images path
val: images/val  # validation images path

# Classes
names:
  0: class1
  1: class2
  2: class3
```

### 3. Train Your Model

```bash
python train.py
```

Or use the web interface for a no-code experience!

---

## ⚙️ Training Configuration

Customize training parameters in `train.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `epochs` | 50 | Number of training epochs |
| `imgsz` | 640 | Input image size |
| `batch` | 16 | Batch size |
| `device` | cpu | Training device (`cpu`, `0`, `0,1` for multi-GPU) |
| `workers` | 4 | Number of data loading workers |
| `pretrained` | True | Use pretrained weights |

### Available YOLO Models

| Model | Size | mAP | Speed |
|-------|------|-----|-------|
| `yolov8n.pt` | Nano | Good | Fastest |
| `yolov8s.pt` | Small | Better | Fast |
| `yolov8m.pt` | Medium | Great | Balanced |
| `yolov8l.pt` | Large | Excellent | Slower |
| `yolov8x.pt` | Extra Large | Best | Slowest |

---

## 📊 Training Outputs

After training, find your results in:

```
runs_stain/
└── yolov8_stain_v1/
    ├── weights/
    │   ├── best.pt      # Best model weights
    │   └── last.pt      # Latest model weights
    ├── results.csv      # Training metrics
    ├── confusion_matrix.png
    ├── results.png      # Training curves
    └── ...
```

### Monitor Training with TensorBoard

```bash
tensorboard --logdir runs_stain
```

---

## 🖥️ Web Interface Features

### Image Annotation Tool
- **Drag-to-draw** bounding boxes
- **Multi-class labeling** with color coding
- **Keyboard shortcuts** for efficiency
- **Zoom and pan** for precise annotations
- **Undo/Redo** functionality
- **Export to YOLO format** with one click

### Training Dashboard
- **Hyperparameter configuration** via intuitive forms
- **Real-time training progress** visualization
- **Model comparison** tools
- **One-click model export**

### Inference Playground
- **Upload images** for instant detection
- **Confidence threshold** adjustment
- **Batch processing** support
- **Download annotated results**

---

## 📁 Project Structure

```
easivisi/
├── dataset/              # Dataset directory
│   ├── images/          # Training and validation images
│   ├── labels/          # YOLO format annotations
│   └── dataset.yaml     # Dataset configuration
├── train.py             # Model training script
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
└── runs_stain/          # Training outputs (generated)
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 .
```

---

## 📝 Roadmap

- [x] YOLOv8 training integration
- [ ] Flask web interface for annotation
- [ ] Real-time training visualization
- [ ] Model export to ONNX, TensorRT
- [ ] Docker containerization
- [ ] REST API for inference
- [ ] Multi-user support with authentication
- [ ] Cloud deployment guides (AWS, GCP, Azure)

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><strong>CUDA out of memory</strong></summary>

Reduce batch size or image size:
```python
model.train(batch=8, imgsz=416)
```
</details>

<details>
<summary><strong>Training is slow on CPU</strong></summary>

For GPU acceleration, install CUDA-enabled PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```
</details>

<details>
<summary><strong>Dataset not found error</strong></summary>

Ensure paths in `dataset.yaml` are correct and relative to the project root.
</details>

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ultralytics](https://ultralytics.com/) for the amazing YOLOv8 framework
- [Flask](https://flask.palletsprojects.com/) for the lightweight web framework
- [PyTorch](https://pytorch.org/) for the deep learning backend

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/ponaalagar/easivisi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ponaalagar/easivisi/discussions)
- **Email**: ponaalagarok@gmail.com

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

**Made with ❤️ for the Computer Vision Community**

[Report Bug](https://github.com/yourusername/easivisi/issues) · [Request Feature](https://github.com/yourusername/easivisi/issues)

</div>

---

## 🔑 Keywords

`yolo` `object-detection` `image-annotation` `flask` `machine-learning` `deep-learning` `computer-vision` `pytorch` `yolov8` `training-pipeline` `annotation-tool` `no-code-ml` `defect-detection` `custom-object-detection` `ai-training` `visual-inspection`
