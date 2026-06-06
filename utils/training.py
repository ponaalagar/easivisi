"""
EasiVisi - Training Utilities
"""
import os
import json
import logging
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

# Configure logger for training module
logger = logging.getLogger("EasiVisi.Training")

# Global training state
_training_jobs = {}
_training_lock = threading.Lock()


class TrainingJob:
    """Represents a training job."""
    
    def __init__(self, job_id, config):
        self.job_id = job_id
        self.config = config
        self.status = 'pending'  # pending, running, completed, failed, stopped
        self.progress = 0
        self.current_epoch = 0
        self.total_epochs = config.get('epochs', 50)
        self.metrics = {}
        self.start_time = None
        self.end_time = None
        self.error = None
        self.save_dir = None
        self._thread = None
        self._stop_flag = False
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'config': self.config,
            'status': self.status,
            'progress': self.progress,
            'current_epoch': self.current_epoch,
            'total_epochs': self.total_epochs,
            'metrics': self.metrics,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'save_dir': self.save_dir
        }


def _run_training(job):
    """Run the training in a background thread."""
    logger.info(f"Training thread started for job {job.job_id}")
    
    try:
        from ultralytics import YOLO
        
        job.status = 'running'
        job.start_time = datetime.now()
        
        # Load model
        model_name = job.config.get('model', 'yolov8n.pt')
        logger.info(f"[{job.job_id}] Loading model: {model_name}")
        model = YOLO(model_name)
        logger.info(f"[{job.job_id}] Model loaded successfully")
        
        # Prepare training arguments
        train_args = {
            'data': job.config['data_yaml'],
            'epochs': job.config.get('epochs', 50),
            'imgsz': job.config.get('imgsz', 640),
            'batch': job.config.get('batch', 16),
            'device': job.config.get('device', 'cpu'),
            'workers': job.config.get('workers', 4),
            'project': job.config.get('project', 'runs'),
            'name': job.config.get('name', f'train_{job.job_id}'),
            'pretrained': job.config.get('pretrained', True),
            'verbose': True
        }
        
        logger.info(f"[{job.job_id}] Training config: epochs={train_args['epochs']}, "
                   f"imgsz={train_args['imgsz']}, batch={train_args['batch']}, "
                   f"device={train_args['device']}")
        logger.info(f"[{job.job_id}] Using dataset: {train_args['data']}")
        
        # Custom callback to update progress
        def on_train_epoch_end(trainer):
            if job._stop_flag:
                logger.info(f"[{job.job_id}] Stop flag detected, interrupting training")
                raise KeyboardInterrupt("Training stopped by user")
            job.current_epoch = trainer.epoch + 1
            job.progress = int((job.current_epoch / job.total_epochs) * 100)
            
            # Update metrics
            if hasattr(trainer, 'metrics'):
                job.metrics = {
                    'box_loss': float(trainer.loss_items[0]) if trainer.loss_items is not None else 0,
                    'cls_loss': float(trainer.loss_items[1]) if trainer.loss_items is not None else 0,
                }
            
            logger.info(f"[{job.job_id}] Epoch {job.current_epoch}/{job.total_epochs} completed ({job.progress}%)")
        
        model.add_callback('on_train_epoch_end', on_train_epoch_end)
        
        # Run training
        logger.info(f"[{job.job_id}] Starting training...")
        results = model.train(**train_args)
        
        job.save_dir = str(results.save_dir)
        job.status = 'completed'
        job.progress = 100
        
        logger.info(f"[{job.job_id}] Training completed successfully! Results saved to: {job.save_dir}")
        
    except KeyboardInterrupt:
        job.status = 'stopped'
        job.error = 'Training stopped by user'
        logger.info(f"[{job.job_id}] Training stopped by user")
    except Exception as e:
        job.status = 'failed'
        job.error = str(e)
        logger.error(f"[{job.job_id}] Training failed with error: {e}")
        logger.error(f"[{job.job_id}] Traceback: {traceback.format_exc()}")
    finally:
        job.end_time = datetime.now()
        duration = (job.end_time - job.start_time).total_seconds() if job.start_time else 0
        logger.info(f"[{job.job_id}] Training job finished. Status: {job.status}, Duration: {duration:.1f}s")


def start_training(config):
    """Start a new training job."""
    job_id = f"job_{int(time.time())}"
    
    logger.info(f"Creating training job {job_id}")
    logger.info(f"Config: dataset_yaml={config.get('data_yaml')}, model={config.get('model')}")
    
    job = TrainingJob(job_id, config)
    
    with _training_lock:
        _training_jobs[job_id] = job
    
    # Start training in background thread
    # NOTE: Thread must NOT be daemon if Flask reloader is enabled,
    # because daemon threads are killed when the main thread exits.
    # However, we've disabled the reloader by default in app.py to avoid this issue.
    thread = threading.Thread(target=_run_training, args=(job,), name=f"TrainingThread-{job_id}")
    thread.daemon = True  # Keep as daemon; Flask reloader is now disabled by default
    job._thread = thread
    thread.start()
    
    logger.info(f"Training thread started for job {job_id}")
    
    return job_id


def get_training_status(job_id):
    """Get status of a training job."""
    with _training_lock:
        job = _training_jobs.get(job_id)
        if job:
            return job.to_dict()
    return None


def stop_training(job_id):
    """Stop a training job."""
    with _training_lock:
        job = _training_jobs.get(job_id)
        if job and job.status == 'running':
            job._stop_flag = True
            return True
    return False


def list_training_jobs():
    """List all training jobs."""
    with _training_lock:
        return [job.to_dict() for job in _training_jobs.values()]


def list_runs(runs_dir):
    """List all training runs from disk."""
    runs = []
    
    if not os.path.exists(runs_dir):
        return runs
    
    for project in os.listdir(runs_dir):
        project_path = os.path.join(runs_dir, project)
        if os.path.isdir(project_path):
            for run in os.listdir(project_path):
                run_path = os.path.join(project_path, run)
                if os.path.isdir(run_path):
                    run_info = {
                        'name': run,
                        'project': project,
                        'path': run_path,
                        'has_weights': os.path.exists(os.path.join(run_path, 'weights', 'best.pt')),
                        'has_results': os.path.exists(os.path.join(run_path, 'results.csv'))
                    }
                    
                    # Get creation time
                    try:
                        run_info['created'] = datetime.fromtimestamp(
                            os.path.getctime(run_path)
                        ).isoformat()
                    except Exception:
                        pass
                    
                    runs.append(run_info)
    
    # Sort by creation time (newest first)
    runs.sort(key=lambda x: x.get('created', ''), reverse=True)
    return runs


def get_run_details(run_path):
    """Get detailed information about a training run."""
    details = {
        'path': run_path,
        'weights': {},
        'results': None,
        'args': None
    }
    
    # Check for weights
    weights_dir = os.path.join(run_path, 'weights')
    if os.path.exists(weights_dir):
        for weight_file in os.listdir(weights_dir):
            if weight_file.endswith('.pt'):
                weight_path = os.path.join(weights_dir, weight_file)
                details['weights'][weight_file] = {
                    'path': weight_path,
                    'size': os.path.getsize(weight_path)
                }
    
    # Check for args.yaml
    args_path = os.path.join(run_path, 'args.yaml')
    if os.path.exists(args_path):
        import yaml
        try:
            with open(args_path, 'r') as f:
                details['args'] = yaml.safe_load(f)
        except Exception:
            pass
    
    # Check for results
    results_path = os.path.join(run_path, 'results.csv')
    if os.path.exists(results_path):
        try:
            import pandas as pd
            df = pd.read_csv(results_path)
            details['results'] = df.to_dict('records')
        except Exception:
            pass
    
    return details
