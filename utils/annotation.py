"""
EasiVisi - Annotation Utilities
"""
import os
from PIL import Image


def parse_yolo_label(label_path):
    """Parse YOLO format label file."""
    annotations = []
    
    if not os.path.exists(label_path):
        return annotations
    
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                annotations.append({
                    'class_id': int(parts[0]),
                    'x_center': float(parts[1]),
                    'y_center': float(parts[2]),
                    'width': float(parts[3]),
                    'height': float(parts[4])
                })
    
    return annotations


def save_yolo_label(label_path, annotations):
    """Save annotations in YOLO format."""
    os.makedirs(os.path.dirname(label_path), exist_ok=True)
    
    with open(label_path, 'w') as f:
        for ann in annotations:
            line = f"{ann['class_id']} {ann['x_center']:.6f} {ann['y_center']:.6f} {ann['width']:.6f} {ann['height']:.6f}\n"
            f.write(line)


def yolo_to_pixel(yolo_box, img_width, img_height):
    """Convert YOLO format (normalized) to pixel coordinates.
    
    Returns annotations in the format expected by the frontend:
    - x, y: top-left corner in pixels
    - width, height: box dimensions in pixels
    - class_id: the class identifier
    """
    x_center = yolo_box['x_center'] * img_width
    y_center = yolo_box['y_center'] * img_height
    width = yolo_box['width'] * img_width
    height = yolo_box['height'] * img_height
    
    # Calculate top-left corner
    x = x_center - width / 2
    y = y_center - height / 2
    
    return {
        'x': x,
        'y': y,
        'width': width,
        'height': height,
        'class_id': yolo_box['class_id']
    }


def pixel_to_yolo(pixel_box, img_width, img_height):
    """Convert pixel coordinates to YOLO format (normalized)."""
    x1, y1, x2, y2 = pixel_box['x1'], pixel_box['y1'], pixel_box['x2'], pixel_box['y2']
    
    # Ensure x1 < x2 and y1 < y2
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    
    width = x2 - x1
    height = y2 - y1
    x_center = x1 + width / 2
    y_center = y1 + height / 2
    
    return {
        'class_id': pixel_box['class_id'],
        'x_center': x_center / img_width,
        'y_center': y_center / img_height,
        'width': width / img_width,
        'height': height / img_height
    }


def get_annotations_for_image(image_path, labels_base_path):
    """Get annotations for an image file."""
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Try different label locations
    possible_paths = [
        os.path.join(labels_base_path, image_name + '.txt'),
        os.path.join(labels_base_path, 'train', image_name + '.txt'),
        os.path.join(labels_base_path, 'val', image_name + '.txt'),
    ]
    
    for label_path in possible_paths:
        if os.path.exists(label_path):
            return parse_yolo_label(label_path), label_path
    
    return [], None


def get_image_with_annotations(image_path, labels_base_path, class_names=None):
    """Get image info with its annotations in pixel format."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception:
        return None
    
    annotations, label_path = get_annotations_for_image(image_path, labels_base_path)
    
    pixel_annotations = []
    for ann in annotations:
        pixel_box = yolo_to_pixel(ann, width, height)
        if class_names and ann['class_id'] < len(class_names):
            pixel_box['class_name'] = class_names[ann['class_id']]
        pixel_annotations.append(pixel_box)
    
    return {
        'image_path': image_path,
        'width': width,
        'height': height,
        'annotations': pixel_annotations,
        'label_path': label_path
    }


def save_annotations_for_image(image_path, labels_base_path, annotations, img_width, img_height):
    """Save annotations for an image in YOLO format."""
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Determine which split the image is in
    image_dir = os.path.dirname(image_path)
    if 'train' in image_dir:
        label_path = os.path.join(labels_base_path, 'train', image_name + '.txt')
    elif 'val' in image_dir:
        label_path = os.path.join(labels_base_path, 'val', image_name + '.txt')
    else:
        label_path = os.path.join(labels_base_path, image_name + '.txt')
    
    # Convert pixel to YOLO format
    yolo_annotations = []
    for ann in annotations:
        # Handle both formats: {x, y, width, height} and {x1, y1, x2, y2}
        if 'x1' in ann:
            # Already in x1, y1, x2, y2 format
            pixel_box = ann
        else:
            # Convert from x, y, width, height format
            pixel_box = {
                'x1': ann['x'],
                'y1': ann['y'],
                'x2': ann['x'] + ann['width'],
                'y2': ann['y'] + ann['height'],
                'class_id': ann['class_id']
            }
        yolo_box = pixel_to_yolo(pixel_box, img_width, img_height)
        yolo_annotations.append(yolo_box)
    
    save_yolo_label(label_path, yolo_annotations)
    return label_path
