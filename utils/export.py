"""
EasiVisi - Model Export Utilities
Export YOLO models to ONNX, TensorRT, and other formats
"""
import os
import logging
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("EasiVisi.Export")

# Export job tracking
_export_jobs = {}
_export_lock = threading.Lock()

# Supported export formats with their configurations
EXPORT_FORMATS = {
    'onnx': {
        'name': 'ONNX',
        'extension': '.onnx',
        'description': 'Open Neural Network Exchange - Cross-platform compatibility',
        'icon': 'fa-cube',
        'requires_gpu': False
    },
    'engine': {
        'name': 'TensorRT',
        'extension': '.engine',
        'description': 'NVIDIA TensorRT - Optimized for NVIDIA GPUs',
        'icon': 'fa-rocket',
        'requires_gpu': True
    },
    'torchscript': {
        'name': 'TorchScript',
        'extension': '.torchscript',
        'description': 'PyTorch TorchScript - Portable PyTorch model',
        'icon': 'fa-fire',
        'requires_gpu': False
    },
    'openvino': {
        'name': 'OpenVINO',
        'extension': '_openvino_model',
        'description': 'Intel OpenVINO - Optimized for Intel hardware',
        'icon': 'fa-microchip',
        'requires_gpu': False
    },
    'coreml': {
        'name': 'CoreML',
        'extension': '.mlpackage',
        'description': 'Apple CoreML - Optimized for Apple devices',
        'icon': 'fa-apple',
        'requires_gpu': False
    },
    'tflite': {
        'name': 'TensorFlow Lite',
        'extension': '.tflite',
        'description': 'TensorFlow Lite - Mobile and edge devices',
        'icon': 'fa-mobile',
        'requires_gpu': False
    }
}


class ExportJob:
    """Represents a model export job."""
    
    def __init__(self, job_id, model_path, export_format, options=None):
        self.job_id = job_id
        self.model_path = model_path
        self.export_format = export_format
        self.options = options or {}
        self.status = 'pending'  # pending, running, completed, failed
        self.progress = 0
        self.start_time = None
        self.end_time = None
        self.error = None
        self.output_path = None
        self.output_size = None
        self._thread = None
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'model_path': self.model_path,
            'export_format': self.export_format,
            'format_info': EXPORT_FORMATS.get(self.export_format, {}),
            'options': self.options,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'output_path': self.output_path,
            'output_size': self.output_size
        }


def _run_export(job):
    """Run the export in a background thread."""
    try:
        from ultralytics import YOLO
        import torch
        
        job.status = 'running'
        job.start_time = datetime.now()
        job.progress = 10
        
        logger.info(f"Starting export job {job.job_id}: {job.model_path} -> {job.export_format}")
        
        # Load the model
        model = YOLO(job.model_path)
        job.progress = 30
        
        # Prepare export arguments
        export_args = {
            'format': job.export_format,
        }
        
        # Add optional parameters
        if 'imgsz' in job.options:
            export_args['imgsz'] = job.options['imgsz']
        if 'half' in job.options:
            export_args['half'] = job.options['half']
        if 'dynamic' in job.options:
            export_args['dynamic'] = job.options['dynamic']
        if 'simplify' in job.options and job.export_format == 'onnx':
            export_args['simplify'] = job.options['simplify']
        if 'opset' in job.options and job.export_format == 'onnx':
            export_args['opset'] = job.options['opset']
        
        # Check GPU availability for TensorRT
        if job.export_format == 'engine' and not torch.cuda.is_available():
            raise RuntimeError("TensorRT export requires NVIDIA GPU with CUDA support")
        
        job.progress = 50
        
        # Run export
        exported_path = model.export(**export_args)
        
        job.progress = 90
        
        # Get output file info
        if exported_path and os.path.exists(str(exported_path)):
            job.output_path = str(exported_path)
            job.output_size = os.path.getsize(str(exported_path))
        else:
            # Try to find the exported file in the same directory
            model_dir = os.path.dirname(job.model_path)
            model_name = os.path.splitext(os.path.basename(job.model_path))[0]
            format_info = EXPORT_FORMATS.get(job.export_format, {})
            ext = format_info.get('extension', '')
            
            potential_path = os.path.join(model_dir, f"{model_name}{ext}")
            if os.path.exists(potential_path):
                job.output_path = potential_path
                job.output_size = os.path.getsize(potential_path)
        
        job.status = 'completed'
        job.progress = 100
        
        logger.info(f"Export job {job.job_id} completed: {job.output_path}")
        
    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        logger.error(f"Export job {job.job_id} failed: {e}")
    finally:
        job.end_time = datetime.now()


def start_export(model_path, export_format, options=None):
    """Start a new export job."""
    import time
    
    # Validate format
    if export_format not in EXPORT_FORMATS:
        raise ValueError(f"Unsupported export format: {export_format}")
    
    # Validate model path
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    job_id = f"export_{int(time.time() * 1000)}"
    
    job = ExportJob(job_id, model_path, export_format, options)
    
    with _export_lock:
        _export_jobs[job_id] = job
    
    # Start export in background thread
    thread = threading.Thread(target=_run_export, args=(job,))
    thread.daemon = True
    job._thread = thread
    thread.start()
    
    return job_id


def get_export_status(job_id):
    """Get status of an export job."""
    with _export_lock:
        job = _export_jobs.get(job_id)
        if job:
            return job.to_dict()
    return None


def list_export_jobs():
    """List all export jobs."""
    with _export_lock:
        return [job.to_dict() for job in _export_jobs.values()]


def get_exported_models(weights_dir):
    """Get list of exported models in a weights directory."""
    exports = []
    
    if not os.path.exists(weights_dir):
        return exports
    
    for filename in os.listdir(weights_dir):
        filepath = os.path.join(weights_dir, filename)
        
        # Check for each export format
        for fmt, info in EXPORT_FORMATS.items():
            ext = info['extension']
            if filename.endswith(ext) or (ext.endswith('_model') and ext[:-6] in filename):
                exports.append({
                    'filename': filename,
                    'path': filepath,
                    'format': fmt,
                    'format_name': info['name'],
                    'size': os.path.getsize(filepath) if os.path.isfile(filepath) else 0,
                    'icon': info['icon']
                })
                break
    
    return exports


def get_available_formats():
    """Get list of available export formats with GPU check."""
    cuda_available = False
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
    except ImportError:
        # torch not available, assume no CUDA
        pass
    
    formats = []
    
    for fmt, info in EXPORT_FORMATS.items():
        format_info = {
            'id': fmt,
            'name': info['name'],
            'description': info['description'],
            'extension': info['extension'],
            'icon': info['icon'],
            'requires_gpu': info['requires_gpu'],
            'available': True if not info['requires_gpu'] else cuda_available
        }
        formats.append(format_info)
    
    return formats


def check_dependencies(export_format):
    """Check if required dependencies for export format are available."""
    issues = []
    
    if export_format == 'engine':
        try:
            import tensorrt
        except ImportError:
            issues.append("TensorRT Python bindings not installed")
        
        try:
            import torch
            if not torch.cuda.is_available():
                issues.append("CUDA not available - TensorRT requires NVIDIA GPU")
        except ImportError:
            issues.append("PyTorch not installed - required for TensorRT export")
    
    elif export_format == 'openvino':
        try:
            import openvino
        except ImportError:
            issues.append("OpenVINO not installed. Install with: pip install openvino")
    
    elif export_format == 'coreml':
        try:
            import coremltools
        except ImportError:
            issues.append("CoreML tools not installed. Install with: pip install coremltools")
    
    elif export_format == 'tflite':
        try:
            import tensorflow
        except ImportError:
            issues.append("TensorFlow not installed. Install with: pip install tensorflow")
    
    return issues
