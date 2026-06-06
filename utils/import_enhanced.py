"""
Enhanced Dataset Import with YAML Support
Simplified single-ZIP import for YOLO datasets
"""
import os
import zipfile
import yaml
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import logging

from config import Config

logger = logging.getLogger("EasiVisi")


def import_yolo_dataset_zip(
    zip_path: str,
    dataset_name: str,
    yaml_content: Optional[str] = None,
    auto_detect_structure: bool = True
) -> Dict:
    """
    Import a complete YOLO dataset from a single ZIP file.
    
    Supports multiple folder structures:
    1. Standard YOLO: images/train, images/val, labels/train, labels/val
    2. Simple: train/, val/ with images and labels mixed
    3. Flat: all images and labels in root
    
    Args:
        zip_path: Path to ZIP file
        dataset_name: Target dataset name
        yaml_content: Optional YAML configuration string
        auto_detect_structure: Auto-detect and reorganize structure
        
    Returns:
        Dict with status, counts, and messages
    """
    
    result = {
        'status': 'success',
        'images_imported': 0,
        'labels_imported': 0,
        'train_images': 0,
        'val_images': 0,
        'classes': [],
        'messages': [],
        'errors': []
    }
    
    dataset_path = os.path.join(Config.DATASET_DIR, dataset_name)
    temp_extract = os.path.join(Config.UPLOAD_DIR, f'temp_import_{dataset_name}')
    
    try:
        # Clean up temp directory if exists
        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract)
        os.makedirs(temp_extract, exist_ok=True)
        
        # Extract ZIP
        logger.info(f"Extracting ZIP to {temp_extract}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract)
        
        # Detect structure
        structure = _detect_dataset_structure(temp_extract)
        logger.info(f"Detected structure: {structure['type']}")
        
        # Process based on structure
        if structure['type'] == 'yolo_standard':
            result = _import_yolo_standard(temp_extract, dataset_path, structure)
        elif structure['type'] == 'mixed':
            result = _import_mixed_structure(temp_extract, dataset_path, structure)
        elif structure['type'] == 'flat':
            result = _import_flat_structure(temp_extract, dataset_path, structure)
        else:
            result['status'] = 'error'
            result['errors'].append("Unsupported ZIP structure")
            return result
        
        # Handle YAML
        if yaml_content:
            _process_yaml_config(dataset_path, yaml_content, result)
        else:
            # Auto-detect or create basic YAML
            _auto_generate_yaml(dataset_path, result)
        
        # Update result
        result['messages'].append(f"Successfully imported dataset '{dataset_name}'")
        result['messages'].append(f"Ready for annotation and training")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        result['status'] = 'error'
        result['errors'].append(str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_extract):
            shutil.rmtree(temp_extract)
    
    return result


def _detect_dataset_structure(extract_path: str) -> Dict:
    """Detect the folder structure of extracted dataset."""
    
    structure = {
        'type': 'unknown',
        'has_images_folder': False,
        'has_labels_folder': False,
        'has_train_val': False,
        'image_files': [],
        'label_files': []
    }
    
    # Scan directory
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)
            
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                structure['image_files'].append(full_path)
            elif ext == '.txt':
                structure['label_files'].append(full_path)
    
    # Check for standard YOLO structure
    images_dir = os.path.join(extract_path, 'images')
    labels_dir = os.path.join(extract_path, 'labels')
    
    if os.path.exists(images_dir):
        structure['has_images_folder'] = True
    if os.path.exists(labels_dir):
        structure['has_labels_folder'] = True
    
    # Check for train/val split
    train_exists = any('train' in p for p in structure['image_files'])
    val_exists = any('val' in p or 'valid' in p for p in structure['image_files'])
    structure['has_train_val'] = train_exists and val_exists
    
    # Determine type
    if structure['has_images_folder'] and structure['has_labels_folder']:
        structure['type'] = 'yolo_standard'
    elif structure['has_train_val']:
        structure['type'] = 'mixed'
    else:
        structure['type'] = 'flat'
    
    return structure


def _import_yolo_standard(temp_path: str, dataset_path: str, structure: Dict) -> Dict:
    """Import standard YOLO structure: images/train, images/val, labels/train, labels/val"""
    
    result = {'images_imported': 0, 'labels_imported': 0, 'train_images': 0, 'val_images': 0}
    
    # Create target structure
    for split in ['train', 'val']:
        os.makedirs(os.path.join(dataset_path, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(dataset_path, 'labels', split), exist_ok=True)
    
    # Copy files
    images_src = os.path.join(temp_path, 'images')
    labels_src = os.path.join(temp_path, 'labels')
    
    if os.path.exists(images_src):
        shutil.copytree(images_src, os.path.join(dataset_path, 'images'), dirs_exist_ok=True)
    
    if os.path.exists(labels_src):
        shutil.copytree(labels_src, os.path.join(dataset_path, 'labels'), dirs_exist_ok=True)
    
    # Count files
    for split in ['train', 'val']:
        img_dir = os.path.join(dataset_path, 'images', split)
        lbl_dir = os.path.join(dataset_path, 'labels', split)
        
        if os.path.exists(img_dir):
            img_count = len([f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
            result['images_imported'] += img_count
            if split == 'train':
                result['train_images'] = img_count
            else:
                result['val_images'] = img_count
        
        if os.path.exists(lbl_dir):
            lbl_count = len([f for f in os.listdir(lbl_dir) if f.endswith('.txt')])
            result['labels_imported'] += lbl_count
    
    return result


def _import_mixed_structure(temp_path: str, dataset_path: str, structure: Dict) -> Dict:
    """Import mixed structure with train/val folders containing both images and labels."""
    
    result = {'images_imported': 0, 'labels_imported': 0, 'train_images': 0, 'val_images': 0}
    
    # Create target structure
    for split in ['train', 'val']:
        os.makedirs(os.path.join(dataset_path, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(dataset_path, 'labels', split), exist_ok=True)
    
    # Process image files
    for img_path in structure['image_files']:
        # Determine split
        if 'train' in img_path.lower():
            split = 'train'
        elif 'val' in img_path.lower() or 'valid' in img_path.lower():
            split = 'val'
        else:
            split = 'train'  # Default
        
        # Copy image
        filename = os.path.basename(img_path)
        dest = os.path.join(dataset_path, 'images', split, filename)
        shutil.copy2(img_path, dest)
        result['images_imported'] += 1
        
        if split == 'train':
            result['train_images'] += 1
        else:
            result['val_images'] += 1
        
        # Copy corresponding label if exists
        label_path = img_path.rsplit('.', 1)[0] + '.txt'
        if os.path.exists(label_path):
            label_dest = os.path.join(dataset_path, 'labels', split, os.path.basename(label_path))
            shutil.copy2(label_path, label_dest)
            result['labels_imported'] += 1
    
    return result


def _import_flat_structure(temp_path: str, dataset_path: str, structure: Dict) -> Dict:
    """Import flat structure - all files in root, will auto-split."""
    
    result = {'images_imported': 0, 'labels_imported': 0, 'train_images': 0, 'val_images': 0}
    
    # Create structure
    os.makedirs(os.path.join(dataset_path, 'images'), exist_ok=True)
    
    # Copy all images to images folder first
    for img_path in structure['image_files']:
        filename = os.path.basename(img_path)
        dest = os.path.join(dataset_path, 'images', filename)
        shutil.copy2(img_path, dest)
        result['images_imported'] += 1
    
    # Copy labels
    labels_dir = os.path.join(dataset_path, 'labels')
    os.makedirs(labels_dir, exist_ok=True)
    
    for lbl_path in structure['label_files']:
        filename = os.path.basename(lbl_path)
        dest = os.path.join(labels_dir, filename)
        shutil.copy2(lbl_path, dest)
        result['labels_imported'] += 1
    
    # Will need to split later
    result['train_images'] = result['images_imported']
    result['messages'] = ['Files imported to root. Use split function to create train/val split.']
    
    return result


def _process_yaml_config(dataset_path: str, yaml_content: str, result: Dict):
    """Process and save YAML configuration."""
    try:
        config = yaml.safe_load(yaml_content)
        
        # Extract classes
        if 'names' in config:
            result['classes'] = config['names'] if isinstance(config['names'], list) else list(config['names'].values())
        
        # Save YAML
        yaml_path = os.path.join(dataset_path, 'dataset.yaml')
        
        # Update paths
        config['path'] = dataset_path
        config['train'] = 'images/train'
        config['val'] = 'images/val'
        
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        result['messages'].append('YAML configuration saved')
        
    except Exception as e:
        result['errors'].append(f'YAML processing error: {str(e)}')


def _auto_generate_yaml(dataset_path: str, result: Dict):
    """Auto-generate dataset.yaml from labels."""
    
    try:
        # Scan labels to find classes
        classes = set()
        labels_dir = os.path.join(dataset_path, 'labels')
        
        if os.path.exists(labels_dir):
            for root, _, files in os.walk(labels_dir):
                for file in files:
                    if file.endswith('.txt'):
                        with open(os.path.join(root, file), 'r') as f:
                            for line in f:
                                parts = line.strip().split()
                                if parts:
                                    classes.add(int(parts[0]))
        
        # Create class names
        class_list = [f'class_{i}' for i in sorted(classes)] if classes else ['object']
        result['classes'] = class_list
        
        # Generate YAML
        yaml_config = {
            'path': dataset_path,
            'train': 'images/train',
            'val': 'images/val',
            'names': class_list
        }
        
        yaml_path = os.path.join(dataset_path, 'dataset.yaml')
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_config, f, default_flow_style=False)
        
        result['messages'].append('Auto-generated dataset.yaml')
        
    except Exception as e:
        result['errors'].append(f'YAML generation error: {str(e)}')
