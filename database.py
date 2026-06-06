"""
EasiVisi - Database Configuration
SQLAlchemy database setup for user authentication and data persistence
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """
    Initialize database with Flask app.
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
