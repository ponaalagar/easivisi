"""
EasiVisi - Quick Start Guide
Complete setup instructions for PostgreSQL + Authentication
"""

# ============================================================================
# STEP 1: Install Dependencies
# ============================================================================

pip install -r requirements.txt

# ============================================================================
# STEP 2: Verify PostgreSQL Connection
# ============================================================================

# Your PostgreSQL should be running on:
# - Host: localhost
# - Port: 5433
# - Database: easivisi
# - User: postgres
# - Password: 936017

# Test connection:
python -c "import psycopg2; psycopg2.connect(host='localhost', port=5433, dbname='easivisi', user='postgres', password='936017'); print('✅ Connected!')"

# ============================================================================
# STEP 3: Initialize Database
# ============================================================================

# This creates all tables and default admin user
python init_db.py

# Expected output:
# ✅ Database connection successful!
# ✅ Tables created successfully!
# ✅ Admin user created!
#    Username: admin
#    Password: Admin@123

# ============================================================================
# STEP 4: Run Application
# ============================================================================

python app.py

# Application will start on http://localhost:5000

# ============================================================================
# STEP 5: Login
# ============================================================================

# Open browser: http://localhost:5000/auth/login
# Username: admin
# Password: Admin@123

# ⚠️ CHANGE PASSWORD IMMEDIATELY after first login!

# ============================================================================
# DATABASE SCHEMA OVERVIEW
# ============================================================================

# Tables created:
# 1. users - User authentication & profiles
# 2. datasets - Dataset management
# 3. dataset_collaborators - Sharing permissions
# 4. training_runs - Training history
# 5. model_exports - Exported models
# 6. activity_logs - Audit trail
# 7. training_metrics - Detailed metrics

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Connection refused?
# → Check PostgreSQL is running: sudo service postgresql status

# Database doesn't exist?
# → Create it: psql -U postgres -c "CREATE DATABASE easivisi;"

# Permission denied?
# → Check user credentials in config.py

# Tables not created?
# → Run: python init_db.py again

# ============================================================================
# NEXT STEPS
# ============================================================================

# 1. Change admin password
# 2. Create your first dataset
# 3. Upload and annotate images
# 4. Train your first YOLO model
# 5. Run inference on new images

# ============================================================================
# USEFUL COMMANDS
# ============================================================================

# View database:
psql -h localhost -p 5433 -U postgres -d easivisi

# List tables:
\dt

# View users:
SELECT username, email, role FROM users;

# Check datasets:
SELECT name, owner_id, total_images FROM datasets;

# ============================================================================
# PRODUCTION DEPLOYMENT
# ============================================================================

# 1. Set environment variables:
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"
export DATABASE_URL="postgresql://user:pass@host:port/db"

# 2. Use production WSGI server:
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# 3. Enable HTTPS
# 4. Configure firewall
# 5. Set up backups for PostgreSQL
