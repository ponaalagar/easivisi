"""
EasiVisi - Dataset Management Utilities

Enterprise-grade dataset management with validation,
error handling, and scalable architecture.
"""
import os
import shutil
import random
import yaml
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from PIL import Image
from config import DATASET_DIR

# Configure module logger
logger = logging.getLogger(__name__)


class ImportStatus(Enum):
    """Import operation status codes."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


@dataclass
class ValidationError:
    """Structured validation error."""
    file: str
    line: Optional[int] = None
    error_type: str = "validation"
    message: str = ""


@dataclass
class ImportResult:
    """Structured import operation result."""
    status: ImportStatus
    total_images: int = 0
    images_with_labels: int = 0
    images_without_labels: int = 0
    total_annotations: int = 0
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    imported_files: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'status': self.status.value,
            'total_images': self.total_images,
            'images_with_labels': self.images_with_labels,
            'images_without_labels': self.images_without_labels,
            'total_annotations': self.total_annotations,
            'errors': [asdict(e) for e in self.errors],
            'warnings': self.warnings,
            'imported_files': self.imported_files
        }


def validate_image(file_path):
    """Validate that file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True, None
    except Exception as e:
        return False, str(e)


def get_image_info(file_path):
    """Get image dimensions and format."""
    try:
        with Image.open(file_path) as img:
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode
            }
    except Exception:
        return None


def create_dataset_structure(dataset_name):
    """Create YOLO dataset directory structure."""
    base_path = os.path.join(DATASET_DIR, dataset_name)
    
    dirs = [
        os.path.join(base_path, 'images', 'train'),
        os.path.join(base_path, 'images', 'val'),
        os.path.join(base_path, 'labels', 'train'),
        os.path.join(base_path, 'labels', 'val'),
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    return base_path


def split_dataset(dataset_name, val_ratio=0.2, seed=42):
    """Split dataset into train/val sets.
    
    Collects all images from the dataset (including from existing train/val folders)
    and redistributes them according to the specified validation ratio.
    """
    base_path = os.path.join(DATASET_DIR, dataset_name)
    images_path = os.path.join(base_path, 'images')
    labels_path = os.path.join(base_path, 'labels')
    
    # Collect ALL images from all possible locations
    all_images = []
    search_paths = [
        images_path,                          # Base images folder
        os.path.join(images_path, 'train'),   # Train folder
        os.path.join(images_path, 'val'),     # Val folder
    ]
    
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for f in os.listdir(search_path):
                file_path = Path(search_path) / f
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    all_images.append(file_path)
    
    if not all_images:
        return {'train': 0, 'val': 0, 'message': 'No images found in dataset'}
    
    # Create directories
    train_img_dir = os.path.join(images_path, 'train')
    val_img_dir = os.path.join(images_path, 'val')
    train_lbl_dir = os.path.join(labels_path, 'train')
    val_lbl_dir = os.path.join(labels_path, 'val')
    
    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(train_lbl_dir, exist_ok=True)
    os.makedirs(val_lbl_dir, exist_ok=True)
    
    # Shuffle and split
    random.seed(seed)
    random.shuffle(all_images)
    
    val_count = max(1, int(len(all_images) * val_ratio))  # At least 1 for validation
    val_images = all_images[:val_count]
    train_images = all_images[val_count:]
    
    train_moved = 0
    val_moved = 0
    
    # Move to train folder
    for img in train_images:
        if img.exists():
            dest = os.path.join(train_img_dir, img.name)
            if str(img) != dest:  # Only move if not already there
                shutil.move(str(img), dest)
            train_moved += 1
            
            # Move corresponding label if exists (check all possible locations)
            for lbl_search in [labels_path, train_lbl_dir, val_lbl_dir]:
                label_file = os.path.join(lbl_search, img.stem + '.txt')
                if os.path.exists(label_file):
                    lbl_dest = os.path.join(train_lbl_dir, img.stem + '.txt')
                    if label_file != lbl_dest:
                        shutil.move(label_file, lbl_dest)
                    break
    
    # Move to val folder
    for img in val_images:
        if img.exists():
            dest = os.path.join(val_img_dir, img.name)
            if str(img) != dest:  # Only move if not already there
                shutil.move(str(img), dest)
            val_moved += 1
            
            # Move corresponding label if exists
            for lbl_search in [labels_path, train_lbl_dir, val_lbl_dir]:
                label_file = os.path.join(lbl_search, img.stem + '.txt')
                if os.path.exists(label_file):
                    lbl_dest = os.path.join(val_lbl_dir, img.stem + '.txt')
                    if label_file != lbl_dest:
                        shutil.move(label_file, lbl_dest)
                    break
    
    return {
        'train': train_moved,
        'val': val_moved,
        'message': f'Split completed: {train_moved} training, {val_moved} validation'
    }


def generate_dataset_yaml(dataset_name, class_names):
    """Generate YOLO dataset.yaml file."""
    base_path = os.path.join(DATASET_DIR, dataset_name)
    
    yaml_content = {
        'path': os.path.abspath(base_path),
        'train': 'images/train',
        'val': 'images/val',
        'names': {i: name for i, name in enumerate(class_names)}
    }
    
    yaml_path = os.path.join(base_path, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)
    
    return yaml_path


def get_dataset_stats(dataset_name):
    """Get statistics for a dataset."""
    base_path = os.path.join(DATASET_DIR, dataset_name)
    
    if not os.path.exists(base_path):
        return None
    
    stats = {
        'name': dataset_name,
        'path': base_path,
        'train_images': 0,
        'val_images': 0,
        'train_labels': 0,
        'val_labels': 0,
        'classes': [],
        'has_yaml': False
    }
    
    # Count images
    train_img_path = os.path.join(base_path, 'images', 'train')
    val_img_path = os.path.join(base_path, 'images', 'val')
    
    if os.path.exists(train_img_path):
        stats['train_images'] = len([f for f in os.listdir(train_img_path) 
                                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))])
    
    if os.path.exists(val_img_path):
        stats['val_images'] = len([f for f in os.listdir(val_img_path) 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))])
    
    # Count labels
    train_lbl_path = os.path.join(base_path, 'labels', 'train')
    val_lbl_path = os.path.join(base_path, 'labels', 'val')
    
    if os.path.exists(train_lbl_path):
        stats['train_labels'] = len([f for f in os.listdir(train_lbl_path) if f.endswith('.txt')])
    
    if os.path.exists(val_lbl_path):
        stats['val_labels'] = len([f for f in os.listdir(val_lbl_path) if f.endswith('.txt')])
    
    # Check for dataset.yaml
    yaml_path = os.path.join(base_path, 'dataset.yaml')
    if os.path.exists(yaml_path):
        stats['has_yaml'] = True
        try:
            with open(yaml_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
                if 'names' in yaml_data:
                    if isinstance(yaml_data['names'], dict):
                        stats['classes'] = list(yaml_data['names'].values())
                    else:
                        stats['classes'] = yaml_data['names']
        except Exception:
            pass
    
    return stats


def list_datasets():
    """List all available datasets."""
    datasets = []
    
    if not os.path.exists(DATASET_DIR):
        return datasets
    
    for item in os.listdir(DATASET_DIR):
        item_path = os.path.join(DATASET_DIR, item)
        if os.path.isdir(item_path):
            stats = get_dataset_stats(item)
            if stats:
                datasets.append(stats)
    
    return datasets


def delete_dataset(dataset_name):
    """Delete a dataset."""
    base_path = os.path.join(DATASET_DIR, dataset_name)
    
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        return True
    return False


# ============================================================================
# INDUSTRY-GRADE IMPORT FUNCTIONALITY
# ============================================================================

def validate_yolo_label_file(label_path: str) -> Tuple[bool, List[ValidationError], int]:
    """
    Validate YOLO format label file with comprehensive error reporting.
    
    YOLO format: class_id x_center y_center width height (normalized [0, 1])
    
    Args:
        label_path: Path to YOLO label file (.txt)
    
    Returns:
        Tuple of (is_valid, errors, num_annotations)
        - is_valid: Boolean indicating if file is valid
        - errors: List of ValidationError objects
        - num_annotations: Number of valid annotations found
    
    Example:
        >>> is_valid, errors, count = validate_yolo_label_file('labels/img1.txt')
        >>> if not is_valid:
        ...     for error in errors:
        ...         print(f"Line {error.line}: {error.message}")
    """
    errors: List[ValidationError] = []
    num_annotations = 0
    
    if not os.path.exists(label_path):
        errors.append(ValidationError(
            file=label_path,
            error_type="file_not_found",
            message="Label file does not exist"
        ))
        return False, errors, 0
    
    try:
        with open(label_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Empty file is valid (no annotations)
        if not lines or all(not line.strip() for line in lines):
            return True, [], 0
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            parts = line.split()
            
            # Check format: must have exactly 5 values
            if len(parts) != 5:
                errors.append(ValidationError(
                    file=os.path.basename(label_path),
                    line=line_num,
                    error_type="format_error",
                    message=f"Expected 5 values (class x y w h), got {len(parts)}"
                ))
                continue
            
            try:
                # Parse values
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Validate class ID (must be non-negative)
                if class_id < 0:
                    errors.append(ValidationError(
                        file=os.path.basename(label_path),
                        line=line_num,
                        error_type="invalid_class",
                        message=f"Class ID must be >= 0, got {class_id}"
                    ))
                    continue
                
                # Validate normalized coordinates [0, 1]
                coords = [x_center, y_center, width, height]
                coord_names = ['x_center', 'y_center', 'width', 'height']
                
                for coord, name in zip(coords, coord_names):
                    if not (0 <= coord <= 1):
                        errors.append(ValidationError(
                            file=os.path.basename(label_path),
                            line=line_num,
                            error_type="invalid_coordinates",
                            message=f"{name}={coord:.4f} is outside [0, 1] range"
                        ))
                        break
                else:
                    # All validations passed for this line
                    num_annotations += 1
                    
            except ValueError as e:
                errors.append(ValidationError(
                    file=os.path.basename(label_path),
                    line=line_num,
                    error_type="parse_error",
                    message=f"Invalid number format: {str(e)}"
                ))
                continue
    
    except Exception as e:
        errors.append(ValidationError(
            file=label_path,
            error_type="read_error",
            message=f"Error reading file: {str(e)}"
        ))
        return False, errors, 0
    
    # File is valid if we have at least some valid annotations or no errors
    is_valid = len(errors) == 0 or num_annotations > 0
    
    return is_valid, errors, num_annotations


def match_images_and_labels(
    image_files: List[str],
    label_files: List[str]
) -> List[Tuple[str, Optional[str]]]:
    """
    Match image files with their corresponding label files by basename.
    
    This function performs intelligent filename matching, handling various
    file extensions and naming patterns commonly found in datasets.
    
    Args:
        image_files: List of image file paths
        label_files: List of label file paths
    
    Returns:
        List of tuples (image_path, label_path or None)
        Each image is paired with its matching label file, or None if no match.
    
    Example:
        >>> images = ['img_001.jpg', 'img_002.png']
        >>> labels = ['img_001.txt', 'img_003.txt']
        >>> matches = match_images_and_labels(images, labels)
        >>> # Returns: [('img_001.jpg', 'img_001.txt'), ('img_002.png', None)]
    """
    logger.info(f"Matching {len(image_files)} images with {len(label_files)} labels")
    
    # Create basename mapping for labels (without extension)
    label_map: Dict[str, str] = {}
    for label_file in label_files:
        basename = os.path.splitext(os.path.basename(label_file))[0]
        label_map[basename] = label_file
    
    # Match each image with its corresponding label
    matched: List[Tuple[str, Optional[str]]] = []
    for image_file in image_files:
        basename = os.path.splitext(os.path.basename(image_file))[0]
        label_file = label_map.get(basename)
        matched.append((image_file, label_file))
    
    matched_count = sum(1 for _, label in matched if label is not None)
    logger.info(f"Matched {matched_count}/{len(image_files)} images with labels")
    
    return matched


def extract_zip_safely(
    zip_path: str,
    extract_to: str,
    allowed_extensions: Optional[List[str]] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Safely extract ZIP file with validation and security checks.
    
    Prevents path traversal attacks and validates file types.
    
    Args:
        zip_path: Path to ZIP file
        extract_to: Destination directory
        allowed_extensions: List of allowed file extensions (optional)
    
    Returns:
        Tuple of (success, extracted_files, errors)
    """
    extracted_files: List[str] = []
    errors: List[str] = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Validate ZIP contents before extraction
            for zip_info in zip_ref.filelist:
                # Prevent path traversal attacks
                if '..' in zip_info.filename or zip_info.filename.startswith('/'):
                    errors.append(f"Unsafe path detected: {zip_info.filename}")
                    continue
                
                # Check file extension if restrictions apply
                if allowed_extensions:
                    ext = os.path.splitext(zip_info.filename)[1].lower()
                    if ext and ext not in allowed_extensions:
                        continue
                
                # Extract file
                try:
                    extracted_path = zip_ref.extract(zip_info, extract_to)
                    if os.path.isfile(extracted_path):
                        extracted_files.append(extracted_path)
                except Exception as e:
                    errors.append(f"Failed to extract {zip_info.filename}: {str(e)}")
        
        logger.info(f"Extracted {len(extracted_files)} files from {zip_path}")
        return len(errors) == 0, extracted_files, errors
        
    except zipfile.BadZipFile:
        errors.append("Invalid or corrupted ZIP file")
        return False, [], errors
    except Exception as e:
        errors.append(f"ZIP extraction error: {str(e)}")
        return False, [], errors


def import_labeled_dataset(
    dataset_name: str,
    images_source: str,
    labels_source: Optional[str],
    source_type: str = 'zip',
    overwrite_existing: bool = False,
    validate_labels: bool = True,
    auto_split: bool = False,
    val_ratio: float = 0.2
) -> ImportResult:
    """
    Import pre-labeled dataset from images and labels sources.
    
    Enterprise-grade import with comprehensive validation, error handling,
    and detailed reporting. Supports both ZIP files and local directories.
    
    Args:
        dataset_name: Target dataset name (must already exist)
        images_source: Path to images ZIP file or directory
        labels_source: Path to labels ZIP file or directory (optional)
        source_type: 'zip' or 'directory'
        overwrite_existing: Whether to overwrite existing files
        validate_labels: Whether to validate YOLO label format
        auto_split: Automatically split into train/val after import
        val_ratio: Validation split ratio if auto_split is True
    
    Returns:
        ImportResult object with detailed statistics and errors
    
    Raises:
        ValueError: If dataset doesn't exist or invalid parameters
        IOError: If source files/directories are not accessible
    
    Example:
        >>> result = import_labeled_dataset(
        ...     dataset_name='my_dataset',
        ...     images_source='images.zip',
        ...     labels_source='labels.zip',
        ...     source_type='zip',
        ...     validate_labels=True
        ... )
        >>> print(f"Imported {result.total_images} images")
        >>> print(f"Errors: {len(result.errors)}")
    """
    logger.info(f"Starting dataset import: {dataset_name}")
    logger.info(f"Source type: {source_type}, Images: {images_source}, Labels: {labels_source}")
    
    result = ImportResult(status=ImportStatus.SUCCESS)
    
    # Validate dataset exists
    dataset_path = os.path.join(DATASET_DIR, dataset_name)
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset not found: {dataset_name}")
        raise ValueError(f"Dataset '{dataset_name}' does not exist. Create it first.")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Extract or collect image files
        image_files: List[str] = []
        label_files: List[str] = []
        
        try:
            if source_type == 'zip':
                # Extract images ZIP
                if not os.path.exists(images_source):
                    raise IOError(f"Images source not found: {images_source}")
                
                allowed_img_ext = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                success, image_files, errors = extract_zip_safely(
                    images_source,
                    os.path.join(temp_dir, 'images'),
                    allowed_img_ext
                )
                
                if errors:
                    for error in errors:
                        result.errors.append(ValidationError(
                            file=images_source,
                            error_type="extraction_error",
                            message=error
                        ))
                
                if not image_files:
                    result.status = ImportStatus.FAILED
                    result.errors.append(ValidationError(
                        file=images_source,
                        error_type="no_images",
                        message="No valid images found in ZIP file"
                    ))
                    logger.error("No images found in source")
                    return result
                
                # Extract labels ZIP if provided
                if labels_source and os.path.exists(labels_source):
                    success, label_files, errors = extract_zip_safely(
                        labels_source,
                        os.path.join(temp_dir, 'labels'),
                        ['.txt']
                    )
                    if errors:
                        for error in errors:
                            result.warnings.append(f"Label extraction: {error}")
                
            elif source_type == 'directory':
                # Collect files from directories
                if not os.path.isdir(images_source):
                    raise IOError(f"Images directory not found: {images_source}")
                
                allowed_ext = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                for root, _, files in os.walk(images_source):
                    for file in files:
                        if Path(file).suffix.lower() in allowed_ext:
                            image_files.append(os.path.join(root, file))
                
                if labels_source and os.path.isdir(labels_source):
                    for root, _, files in os.walk(labels_source):
                        for file in files:
                            if file.endswith('.txt'):
                                label_files.append(os.path.join(root, file))
            else:
                raise ValueError(f"Invalid source_type: {source_type}. Use 'zip' or 'directory'")
            
            # Match images with labels
            matched_pairs = match_images_and_labels(image_files, label_files)
            
            # Import each image-label pair
            dest_images_dir = os.path.join(dataset_path, 'images')
            dest_labels_dir = os.path.join(dataset_path, 'labels')
            os.makedirs(dest_images_dir, exist_ok=True)
            os.makedirs(dest_labels_dir, exist_ok=True)
            
            for img_path, lbl_path in matched_pairs:
                img_name = os.path.basename(img_path)
                img_dest = os.path.join(dest_images_dir, img_name)
                
                # Check if image already exists
                if os.path.exists(img_dest) and not overwrite_existing:
                    result.warnings.append(f"Skipped existing image: {img_name}")
                    continue
                
                # Validate image
                is_valid, error = validate_image(img_path)
                if not is_valid:
                    result.errors.append(ValidationError(
                        file=img_name,
                        error_type="invalid_image",
                        message=error or "Image validation failed"
                    ))
                    continue
                
                # Copy image
                try:
                    shutil.copy2(img_path, img_dest)
                    result.total_images += 1
                    
                    file_info: Dict[str, Any] = {
                        'image': img_name,
                        'label': None,
                        'num_annotations': 0,
                        'has_errors': False
                    }
                    
                    # Process label if available
                    if lbl_path:
                        # Validate label if requested
                        if validate_labels:
                            is_valid, lbl_errors, num_annot = validate_yolo_label_file(lbl_path)
                            
                            if lbl_errors:
                                result.errors.extend(lbl_errors)
                                file_info['has_errors'] = True
                            
                            if is_valid or num_annot > 0:
                                # Copy label even if there are some errors but valid annotations exist
                                lbl_name = os.path.splitext(img_name)[0] + '.txt'
                                lbl_dest = os.path.join(dest_labels_dir, lbl_name)
                                shutil.copy2(lbl_path, lbl_dest)
                                
                                result.images_with_labels += 1
                                result.total_annotations += num_annot
                                file_info['label'] = lbl_name
                                file_info['num_annotations'] = num_annot
                        else:
                            # Copy without validation
                            lbl_name = os.path.splitext(img_name)[0] + '.txt'
                            lbl_dest = os.path.join(dest_labels_dir, lbl_name)
                            shutil.copy2(lbl_path, lbl_dest)
                            result.images_with_labels += 1
                            file_info['label'] = lbl_name
                    
                    if not lbl_path:
                        result.images_without_labels += 1
                    
                    result.imported_files.append(file_info)
                    
                except Exception as e:
                    result.errors.append(ValidationError(
                        file=img_name,
                        error_type="copy_error",
                        message=f"Failed to copy file: {str(e)}"
                    ))
                    logger.error(f"Error importing {img_name}: {e}")
            
            # Auto-split if requested
            if auto_split and result.total_images > 0:
                logger.info(f"Auto-splitting dataset with ratio {val_ratio}")
                try:
                    split_result = split_dataset(dataset_name, val_ratio)
                    result.warnings.append(f"Auto-split: {split_result.get('message', '')}")
                except Exception as e:
                    result.warnings.append(f"Auto-split failed: {str(e)}")
            
        except Exception as e:
            logger.exception(f"Import failed: {e}")
            result.status = ImportStatus.FAILED
            result.errors.append(ValidationError(
                file="import",
                error_type="system_error",
                message=str(e)
            ))
            return result
    
    # Determine final status
    if result.total_images == 0:
        result.status = ImportStatus.FAILED
    elif len(result.errors) > 0:
        result.status = ImportStatus.PARTIAL_SUCCESS
    else:
        result.status = ImportStatus.SUCCESS
    
    logger.info(f"Import completed: {result.status.value}")
    logger.info(f"Images: {result.total_images}, With labels: {result.images_with_labels}")
    logger.info(f"Annotations: {result.total_annotations}, Errors: {len(result.errors)}")
    
    return result
