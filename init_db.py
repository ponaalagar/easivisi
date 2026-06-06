"""
EasiVisi - Database Initialization Script
Creates all tables and initial admin user
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.user import User

def init_database():
    """Initialize database and create tables."""
    with app.app_context():
        print("🔧 Creating database tables...")
        db.create_all()
        print("✅ Tables created successfully!")
        
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("ℹ️  Admin user already exists")
        else:
            # Create default admin user
            print("👤 Creating admin user...")
            admin = User(
                username='admin',
                email='admin@easivisi.local',
                full_name='System Administrator',
                role='admin',
                is_active=True,
                is_verified=True
            )
            admin.set_password('Admin@123')  # CHANGE THIS!
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created!")
            print("   Username: admin")
            print("   Password: Admin@123")
            print("   ⚠️  CHANGE PASSWORD IMMEDIATELY!")

def test_connection():
    """Test database connection."""
    with app.app_context():
        try:
            db.engine.connect()
            print("✅ Database connection successful!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("EasiVisi - Database Initialization")
    print("=" * 60)
    
    if test_connection():
        init_database()
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
    else:
        print("\n❌ Please check your PostgreSQL configuration")
        sys.exit(1)
