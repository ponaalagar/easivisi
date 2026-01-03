"""
EasiVisi - Visual AI Training Platform
Flask Web Application
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename

from config import Config, get_config
from utils.dataset import (
    create_dataset_structure, split_dataset, generate_dataset_yaml,
    get_dataset_stats, list_datasets, delete_dataset, validate_image
)
from utils.annotation import (
    get_image_with_annotations, save_annotations_for_image,
    parse_yolo_label, save_yolo_label
)
from utils.training import (
    start_training, get_training_status, stop_training,
    list_training_jobs, list_runs, get_run_details
)
from utils.inference import (
    detect_from_bytes, draw_predictions_bytes, list_available_models
)


app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# ===================
# Logging Setup
# ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger("EasiVisi")


# ===================
# Helper Functions
# ===================

def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_IMAGE_EXTENSIONS


# ===================
# Page Routes
# ===================

@app.route('/')
def index():
    """Landing page."""
    logger.info("Rendering index page.")
    datasets = list_datasets()
    runs = list_runs(Config.RUNS_DIR)
    return render_template('index.html', datasets=datasets, runs=runs)


@app.route('/dataset')
def dataset_page():
    """Dataset management page."""
    logger.info("Rendering dataset management page.")
    datasets = list_datasets()
    return render_template('dataset.html', datasets=datasets)


@app.route('/dataset/<dataset_name>')
def dataset_detail(dataset_name):
    """Dataset detail page."""
    logger.info(f"Rendering detail page for dataset: {dataset_name}")
    stats = get_dataset_stats(dataset_name)
    if not stats:
        logger.warning(f"Dataset not found: {dataset_name}")
        return redirect(url_for('dataset_page'))
    return render_template('dataset_detail.html', dataset=stats)


@app.route('/annotate/<dataset_name>')
def annotate_page(dataset_name):
    """Annotation tool page."""
    logger.info(f"Rendering annotation tool for dataset: {dataset_name}")
    stats = get_dataset_stats(dataset_name)
    if not stats:
        logger.warning(f"Dataset not found for annotation: {dataset_name}")
        return redirect(url_for('dataset_page'))
    return render_template('annotate.html', dataset=stats)


@app.route('/train')
def train_page():
    """Training configuration page."""
    logger.info("Rendering training configuration page.")
    datasets = list_datasets()
    models = Config.YOLO_MODELS
    jobs = list_training_jobs()
    return render_template('train.html', datasets=datasets, models=models, jobs=jobs)


@app.route('/inference')
def inference_page():
    """Inference playground page."""
    logger.info("Rendering inference playground page.")
    models = list_available_models(Config.MODELS_DIR, Config.RUNS_DIR)
    return render_template('inference.html', models=models)


@app.route('/runs')
def runs_page():
    """Training runs history page."""
    logger.info("Rendering training runs history page.")
    runs = list_runs(Config.RUNS_DIR)
    return render_template('runs.html', runs=runs)


# ===================
# API Routes - Dataset
# ===================

@app.route('/api/dataset/create', methods=['POST'])
def api_create_dataset():
    """Create a new dataset."""
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        logger.warning("Dataset creation failed: name is required.")
        return jsonify({'error': 'Dataset name is required'}), 400
    
    # Sanitize name
    name = secure_filename(name)
    
    try:
        path = create_dataset_structure(name)
        logger.info(f"Created dataset: {name} at {path}")
        return jsonify({'success': True, 'path': path, 'name': name})
    except Exception as e:
        logger.error(f"Error creating dataset {name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<dataset_name>/upload', methods=['POST'])
def api_upload_images(dataset_name):
    """Upload images to a dataset."""
    if 'files' not in request.files:
        logger.warning(f"No files provided for upload to dataset: {dataset_name}")
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded = []
    errors = []
    
    # Determine destination
    dest_dir = os.path.join(Config.DATASET_DIR, dataset_name, 'images')
    os.makedirs(dest_dir, exist_ok=True)
    
    for file in files:
        if file and allowed_image(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(dest_dir, filename)
            file.save(filepath)
            
            # Validate
            valid, err = validate_image(filepath)
            if valid:
                uploaded.append(filename)
            else:
                os.remove(filepath)
                errors.append({'file': filename, 'error': err})
        else:
            errors.append({'file': file.filename, 'error': 'Invalid file type'})
    logger.info(f"Uploaded {len(uploaded)} images to dataset {dataset_name}. Errors: {len(errors)}")
    return jsonify({
        'uploaded': uploaded,
        'errors': errors,
        'count': len(uploaded)
    })


@app.route('/api/dataset/<dataset_name>/split', methods=['POST'])
def api_split_dataset(dataset_name):
    """Split dataset into train/val."""
    data = request.get_json() or {}
    val_ratio = data.get('val_ratio', 0.2)
    try:
        result = split_dataset(dataset_name, val_ratio)
        logger.info(f"Split dataset {dataset_name} with val_ratio={val_ratio}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error splitting dataset {dataset_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<dataset_name>/yaml', methods=['POST'])
def api_generate_yaml(dataset_name):
    """Generate dataset.yaml file."""
    data = request.get_json()
    class_names = data.get('classes', [])
    
    if not class_names:
        logger.warning(f"No class names provided for dataset {dataset_name}.")
        return jsonify({'error': 'At least one class name is required'}), 400
    
    try:
        yaml_path = generate_dataset_yaml(dataset_name, class_names)
        logger.info(f"Generated dataset.yaml for {dataset_name} at {yaml_path}")
        return jsonify({'success': True, 'path': yaml_path})
    except Exception as e:
        logger.error(f"Error generating dataset.yaml for {dataset_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dataset/<dataset_name>/stats')
def api_dataset_stats(dataset_name):
    """Get dataset statistics."""
    stats = get_dataset_stats(dataset_name)
    if stats:
        return jsonify(stats)
    logger.warning(f"Dataset stats not found for {dataset_name}")
    return jsonify({'error': 'Dataset not found'}), 404


@app.route('/api/dataset/<dataset_name>/images')
def api_list_images(dataset_name):
    """List all images in a dataset."""
    base_path = os.path.join(Config.DATASET_DIR, dataset_name, 'images')
    labels_base = os.path.join(Config.DATASET_DIR, dataset_name, 'labels')
    images = []
    annotated_count = 0
    
    # Check all locations
    for subdir in ['', 'train', 'val']:
        check_path = os.path.join(base_path, subdir) if subdir else base_path
        labels_path = os.path.join(labels_base, subdir) if subdir else labels_base
        if os.path.exists(check_path):
            for f in os.listdir(check_path):
                if f.lower().endswith(tuple(Config.ALLOWED_IMAGE_EXTENSIONS)):
                    # Check if label file exists
                    label_name = os.path.splitext(f)[0] + '.txt'
                    label_file = os.path.join(labels_path, label_name)
                    has_annotation = os.path.exists(label_file) and os.path.getsize(label_file) > 0
                    if has_annotation:
                        annotated_count += 1
                    images.append({
                        'name': f,
                        'path': os.path.join(subdir, f) if subdir else f,
                        'split': subdir or 'unsplit',
                        'annotated': has_annotation
                    })
    logger.info(f"Listed {len(images)} images for dataset {dataset_name}.")
    return jsonify({
        'images': images,
        'total': len(images),
        'annotated': annotated_count,
        'remaining': len(images) - annotated_count
    })


@app.route('/api/dataset/<dataset_name>/delete', methods=['DELETE'])
def api_delete_dataset(dataset_name):
    """Delete a dataset."""
    try:
        if delete_dataset(dataset_name):
            logger.info(f"Deleted dataset: {dataset_name}")
            return jsonify({'success': True})
        logger.warning(f"Attempted to delete non-existent dataset: {dataset_name}")
        return jsonify({'error': 'Dataset not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting dataset {dataset_name}: {e}")
        return jsonify({'error': str(e)}), 500


# ===================
# API Routes - Annotation
# ===================

@app.route('/api/annotate/<dataset_name>/<path:image_path>')
def api_get_annotation(dataset_name, image_path):
    """Get image with annotations."""
    base_path = os.path.join(Config.DATASET_DIR, dataset_name)
    img_full_path = os.path.join(base_path, 'images', image_path)
    labels_path = os.path.join(base_path, 'labels')
    # Get class names from yaml if available
    class_names = []
    stats = get_dataset_stats(dataset_name)
    if stats:
        class_names = stats.get('classes', [])
    result = get_image_with_annotations(img_full_path, labels_path, class_names)
    if result:
        # Convert path to relative URL
        result['image_url'] = f'/dataset/{dataset_name}/image/{image_path}'
        logger.info(f"Fetched annotation for image {image_path} in dataset {dataset_name}")
        return jsonify(result)
    logger.warning(f"Image not found for annotation: {image_path} in dataset {dataset_name}")
    return jsonify({'error': 'Image not found'}), 404


@app.route('/api/annotate/<dataset_name>/<path:image_path>', methods=['POST'])
def api_save_annotation(dataset_name, image_path):
    """Save annotations for an image."""
    data = request.get_json()
    annotations = data.get('annotations', [])
    img_width = data.get('width')
    img_height = data.get('height')
    if not img_width or not img_height:
        logger.warning(f"Image dimensions required for annotation save: {image_path} in {dataset_name}")
        return jsonify({'error': 'Image dimensions required'}), 400
    base_path = os.path.join(Config.DATASET_DIR, dataset_name)
    img_full_path = os.path.join(base_path, 'images', image_path)
    labels_path = os.path.join(base_path, 'labels')
    try:
        label_path = save_annotations_for_image(
            img_full_path, labels_path, annotations, img_width, img_height
        )
        logger.info(f"Saved annotation for image {image_path} in dataset {dataset_name}")
        return jsonify({'success': True, 'label_path': label_path})
    except Exception as e:
        logger.error(f"Error saving annotation for {image_path} in {dataset_name}: {e}")
        return jsonify({'error': str(e)}), 500


# ===================
# API Routes - Training
# ===================

@app.route('/api/train/start', methods=['POST'])
def api_start_training():
    """Start a training job."""
    data = request.get_json()
    required = ['dataset', 'model']
    for field in required:
        if field not in data:
            logger.warning(f"Training start failed: {field} is required.")
            return jsonify({'error': f'{field} is required'}), 400
    # Build config
    dataset_name = data['dataset']
    stats = get_dataset_stats(dataset_name)
    if not stats:
        logger.warning(f"Training start failed: dataset not found: {dataset_name}")
        return jsonify({'error': 'Dataset not found'}), 404
    if not stats.get('has_yaml'):
        logger.warning(f"Training start failed: dataset YAML not found for {dataset_name}")
        return jsonify({'error': 'Dataset YAML not found. Please configure classes first.'}), 400
    config = {
        'data_yaml': os.path.join(Config.DATASET_DIR, dataset_name, 'dataset.yaml'),
        'model': data.get('model', 'yolov8n.pt'),
        'epochs': int(data.get('epochs', 50)),
        'imgsz': int(data.get('imgsz', 640)),
        'batch': int(data.get('batch', 16)),
        'device': data.get('device', 'cpu'),
        'workers': int(data.get('workers', 4)),
        'project': Config.RUNS_DIR,
        'name': data.get('name', dataset_name),
        'pretrained': data.get('pretrained', True)
    }
    try:
        job_id = start_training(config)
        logger.info(f"Started training job {job_id} for dataset {dataset_name}")
        return jsonify({'success': True, 'job_id': job_id})
    except Exception as e:
        logger.error(f"Error starting training for {dataset_name}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/train/status/<job_id>')
def api_training_status(job_id):
    """Get training job status."""
    status = get_training_status(job_id)
    if status:
        return jsonify(status)
    logger.warning(f"Training job status not found: {job_id}")
    return jsonify({'error': 'Job not found'}), 404


@app.route('/api/train/stop/<job_id>', methods=['POST'])
def api_stop_training(job_id):
    """Stop a training job."""
    if stop_training(job_id):
        logger.info(f"Stopped training job: {job_id}")
        return jsonify({'success': True})
    logger.warning(f"Attempted to stop non-existent or not running job: {job_id}")
    return jsonify({'error': 'Job not found or not running'}), 404


@app.route('/api/train/jobs')
def api_list_jobs():
    """List all training jobs."""
    jobs = list_training_jobs()
    logger.info(f"Listed {len(jobs)} training jobs.")
    return jsonify({'jobs': jobs})


@app.route('/api/runs')
def api_list_runs():
    """List all training runs."""
    runs = list_runs(Config.RUNS_DIR)
    logger.info(f"Listed {len(runs)} training runs.")
    return jsonify({'runs': runs})


@app.route('/api/runs/<path:run_path>')
def api_run_details(run_path):
    """Get details of a training run."""
    full_path = os.path.join(Config.RUNS_DIR, run_path)
    if os.path.exists(full_path):
        details = get_run_details(full_path)
        logger.info(f"Fetched details for run: {run_path}")
        return jsonify(details)
    logger.warning(f"Run not found: {run_path}")
    return jsonify({'error': 'Run not found'}), 404


# ===================
# API Routes - Inference
# ===================

@app.route('/api/inference/detect', methods=['POST'])
def api_detect():
    """Run detection on uploaded image."""
    if 'image' not in request.files:
        logger.warning("Detection failed: No image provided.")
        return jsonify({'error': 'No image provided'}), 400
    model_path = request.form.get('model')
    if not model_path:
        logger.warning("Detection failed: Model path required.")
        return jsonify({'error': 'Model path required'}), 400
    conf = float(request.form.get('confidence', 0.25))
    file = request.files['image']
    image_bytes = file.read()
    try:
        detections, width, height = detect_from_bytes(model_path, image_bytes, conf)
        result_image = draw_predictions_bytes(image_bytes, detections)
        logger.info(f"Detection run on image with model {model_path}, {len(detections)} detections.")
        return jsonify({
            'detections': detections,
            'count': len(detections),
            'width': width,
            'height': height,
            'result_image': f'data:image/jpeg;base64,{result_image}'
        })
    except Exception as e:
        logger.error(f"Error during detection: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/models')
def api_list_models():
    """List available models."""
    models = list_available_models(Config.MODELS_DIR, Config.RUNS_DIR)
    logger.info(f"Listed {len(models)} available models.")
    return jsonify({'models': models})


# ===================
# Static File Serving
# ===================

@app.route('/dataset/<dataset_name>/image/<path:image_path>')
def serve_dataset_image(dataset_name, image_path):
    """Serve dataset images."""
    base_path = os.path.join(Config.DATASET_DIR, dataset_name, 'images')
    logger.info(f"Serving image {image_path} from dataset {dataset_name}")
    return send_from_directory(base_path, image_path)


# ===================
# Error Handlers
# ===================

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 Not Found: {request.path}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 Internal Server Error: {request.path} - {e}")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error='Internal server error'), 500


# ===================
# Main Entry Point
# ===================

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("EasiVisi - Visual AI Training Platform")
    logger.info("=" * 50)
    logger.info(f"Dataset Directory: {Config.DATASET_DIR}")
    logger.info(f"Runs Directory: {Config.RUNS_DIR}")
    logger.info("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
