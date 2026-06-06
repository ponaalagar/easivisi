"""
EasiVisi - Configuration Management
Database and application settings.
"""
import os
import socket
from pathlib import Path

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
RUNS_DIR = os.path.join(BASE_DIR, 'runs')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Ensure directories exist
for dir_path in [DATASET_DIR, RUNS_DIR, MODELS_DIR, UPLOAD_DIR]:
    os.makedirs(dir_path, exist_ok=True)


# ============================================================================
# POSTGRESQL DATABASE CONFIGURATION (User's Settings)
# ============================================================================

def _postgres_is_available(host, port, timeout=1.0):
    """Return True when a PostgreSQL server accepts TCP connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def build_database_settings(env=None, probe=None):
    """Build SQLAlchemy settings with a PostgreSQL-first, SQLite fallback strategy."""
    env = os.environ if env is None else env
    probe = _postgres_is_available if probe is None else probe

    db_host = env.get("ALLOWANCE_DB_HOST", env.get("DB_HOST", "localhost"))
    db_port = int(env.get("ALLOWANCE_DB_PORT", env.get("DB_PORT", "5433")))
    db_name = env.get("ALLOWANCE_DB_NAME", env.get("DB_NAME", "easivisi"))
    db_user = env.get("ALLOWANCE_DB_USER", env.get("DB_USER", "postgres"))
    db_password = env.get("ALLOWANCE_DB_PASSWORD", env.get("DB_PASSWORD", "936017"))
    require_postgres = env.get("EASIVISI_REQUIRE_POSTGRES", "").lower() in {"1", "true", "yes", "on"}

    postgres_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    postgres_options = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }

    if probe(db_host, db_port, timeout=float(env.get("EASIVISI_DB_PROBE_TIMEOUT", "1.0"))):
        return {
            'SQLALCHEMY_DATABASE_URI': postgres_uri,
            'SQLALCHEMY_ENGINE_OPTIONS': postgres_options,
            'DATABASE_BACKEND': 'postgresql',
        }

    if require_postgres:
        raise RuntimeError(
            f"PostgreSQL is not reachable at {db_host}:{db_port}. "
            "Set EASIVISI_REQUIRE_POSTGRES=0 or start the database server."
        )

    sqlite_path = Path(env.get("EASIVISI_SQLITE_PATH", os.path.join(BASE_DIR, "easivisi.db"))).resolve()
    sqlite_uri = f"sqlite:///{sqlite_path.as_posix()}"

    return {
        'SQLALCHEMY_DATABASE_URI': sqlite_uri,
        'SQLALCHEMY_ENGINE_OPTIONS': {},
        'DATABASE_BACKEND': 'sqlite',
    }


DATABASE_SETTINGS = build_database_settings()
SQLALCHEMY_DATABASE_URI = DATABASE_SETTINGS['SQLALCHEMY_DATABASE_URI']
SQLALCHEMY_ENGINE_OPTIONS = DATABASE_SETTINGS['SQLALCHEMY_ENGINE_OPTIONS']
DATABASE_BACKEND = DATABASE_SETTINGS['DATABASE_BACKEND']


# ============================================================================
# FLASK & SECURITY CONFIGURATION
# ============================================================================

class Config:
    """Main application configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'easivisi-dev-key-change-in-prod-v2024')
    
    # Database settings (PostgreSQL preferred, SQLite fallback)
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS
    DATABASE_BACKEND = DATABASE_BACKEND
    SQLALCHEMY_ECHO = os.getenv('FLASK_ENV') == 'development'
    
    # Security settings
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Remember me cookie
    REMEMBER_COOKIE_DURATION = 604800  # 7 days
    REMEMBER_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ALLOWED_MODEL_EXTENSIONS = {'.pt', '.onnx'}
    
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
    
    # Available YOLO models
    YOLO_MODELS = {
        'yolov8n.pt': {'name': 'YOLOv8n', 'params': '3.2M', 'speed': 'Fastest', 'accuracy': 'Good'},
        'yolov8s.pt': {'name': 'YOLOv8s', 'params': '11.2M', 'speed': 'Fast', 'accuracy': 'Better'},
        'yolov8m.pt': {'name': 'YOLOv8m', 'params': '25.9M', 'speed': 'Medium', 'accuracy': 'Great'},
        'yolov8l.pt': {'name': 'YOLOv8l', 'params': '43.7M', 'speed': 'Slow', 'accuracy': 'Excellent'},
        'yolov8x.pt': {'name': 'YOLOv8x', 'params': '68.2M', 'speed': 'Slowest', 'accuracy': 'Highest'},
    }


def get_config():
    """Get configuration object."""
    return Config


# Print config for verification (development only)
if os.getenv('FLASK_ENV') == 'development':
    print(f"🔧 Database backend: {DATABASE_BACKEND}")
    print(f"🔧 Database URI: {SQLALCHEMY_DATABASE_URI}")
