"""
EasiVisi - Complete Database Schema
All database models for the application
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from database import db


# ============================================================================
# USER MANAGEMENT
# ============================================================================

class User(db.Model, UserMixin):
    """User account model with authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    full_name = db.Column(db.String(150))
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expires = db.Column(db.DateTime)
    api_key = db.Column(db.String(64), unique=True)
    
    # Relationships
    datasets = db.relationship('Dataset', backref='owner', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Dataset.owner_id')
    training_runs = db.relationship('TrainingRun', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def has_permission(self, permission):
        permissions = {
            'admin': ['create', 'read', 'update', 'delete', 'manage_users', 'export'],
            'user': ['create', 'read', 'update', 'delete', 'export'],
            'viewer': ['read']
        }
        return permission in permissions.get(self.role, [])
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


# ============================================================================
# DATASET MANAGEMENT
# ============================================================================

class Dataset(db.Model):
    """Dataset model for tracking user datasets."""
    
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    
    # Dataset statistics
    total_images = db.Column(db.Integer, default=0)
    train_images = db.Column(db.Integer, default=0)
    val_images = db.Column(db.Integer, default=0)
    num_classes = db.Column(db.Integer, default=0)
    classes = db.Column(db.JSON)  # Store class names as JSON array
    
    # Paths
    dataset_path = db.Column(db.String(500))
    yaml_path = db.Column(db.String(500))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_modified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    training_runs = db.relationship('TrainingRun', backref='dataset', lazy='dynamic', cascade='all, delete-orphan')
    collaborators = db.relationship('DatasetCollaborator', backref='dataset', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Dataset {self.name}>'


class DatasetCollaborator(db.Model):
    """Collaboration permissions for datasets."""
    
    __tablename__ = 'dataset_collaborators'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='view')  # 'view', 'edit', 'admin'
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    __table_args__ = (
        db.UniqueConstraint('dataset_id', 'user_id', name='unique_dataset_user'),
    )


# ============================================================================
# TRAINING & MODEL MANAGEMENT
# ============================================================================

class TrainingRun(db.Model):
    """Training run metadata and results."""
    
    __tablename__ = 'training_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_name = db.Column(db.String(100), nullable=False, index=True)
    run_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Model configuration
    model_name = db.Column(db.String(50))
    epochs = db.Column(db.Integer)
    batch_size = db.Column(db.Integer)
    img_size = db.Column(db.Integer)
    device = db.Column(db.String(20))
    
    # Training status
    status = db.Column(db.String(20))  # 'pending', 'running', 'completed', 'failed', 'stopped'
    progress = db.Column(db.Float, default=0.0)
    
    # Results
    final_map = db.Column(db.Float)
    final_map50 = db.Column(db.Float)
    final_loss = db.Column(db.Float)
    training_time = db.Column(db.Integer)  # seconds
    
    # Paths
    weights_path = db.Column(db.String(500))
    results_path = db.Column(db.String(500))
    
    # Metadata
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    exports = db.relationship('ModelExport', backref='training_run', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TrainingRun {self.run_name}>'


class ModelExport(db.Model):
    """Exported model formats (ONNX, TensorRT, etc.)."""
    
    __tablename__ = 'model_exports'
    
    id = db.Column(db.Integer, primary_key=True)
    training_run_id = db.Column(db.Integer, db.ForeignKey('training_runs.id'), nullable=False)
    
    format = db.Column(db.String(20), nullable=False)  # 'onnx', 'torchscript', 'tflite', 'engine'
    export_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)  # bytes
    
    exported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    exported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ModelExport {self.format}>'


# ============================================================================
# ANALYTICS & AUDIT
# ============================================================================

class ActivityLog(db.Model):
    """Audit log for user activities."""
    
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    action = db.Column(db.String(50), nullable=False)  # 'login', 'create_dataset', 'start_training', etc.
    resource_type = db.Column(db.String(50))  # 'dataset', 'training_run', 'user'
    resource_id = db.Column(db.Integer)
    
    details = db.Column(db.JSON)  # Additional metadata
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class TrainingMetrics(db.Model):
    """Detailed training metrics for analytics."""
    
    __tablename__ = 'training_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    training_run_id = db.Column(db.Integer, db.ForeignKey('training_runs.id'), nullable=False)
    
    epoch = db.Column(db.Integer)
    train_loss = db.Column(db.Float)
    val_loss = db.Column(db.Float)
    map50 = db.Column(db.Float)
    map = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('training_run_id', 'epoch', name='unique_training_epoch'),
    )


# ============================================================================
# INDEXES FOR PERFORMANCE
# ============================================================================

# Create indexes
db.Index('ix_datasets_owner_created', Dataset.owner_id, Dataset.created_at)
db.Index('ix_training_runs_creator_started', TrainingRun.creator_id, TrainingRun.started_at)
db.Index('ix_activity_logs_user_created', ActivityLog.user_id, ActivityLog.created_at)
