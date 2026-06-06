# PostgreSQL Setup Instructions

## 1. Install PostgreSQL
- **Windows:** Download from https://www.postgresql.org/download/windows/
- **Mac:** `brew install postgresql`
- **Linux:** `sudo apt-get install postgresql postgresql-contrib`

## 2. Create Database and User

```bash
# Access PostgreSQL as postgres user
psql -U postgres

# In psql shell:
CREATE DATABASE easivisi_db;
CREATE USER easivisi_user WITH PASSWORD 'easivisi_pass';
GRANT ALL PRIVILEGES ON DATABASE easivisi_db TO easivisi_user;
\q
```

## 3. Alternative: Use Environment Variable

Set custom database URL:
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://your_user:your_pass@localhost:5432/your_db"

# Linux/Mac
export DATABASE_URL="postgresql://your_user:your_pass@localhost:5432/your_db"
```

## 4. Initialize Database

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration with User model"

# Apply migration
flask db upgrade
```

## 5. Create Admin User (Run Once)

```python
# create_admin.py
from app import app
from database import db
from models.user import User

with app.app_context():
    admin = User(
        username='admin',
        email='admin@easivisi.local',
        full_name='Administrator',
        role='admin',
        is_active=True,
        is_verified=True
    )
    admin.set_password('Admin@123')  # CHANGE THIS!
    
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
```

Run: `python create_admin.py`

## 6. Verify Connection

```python
# test_db.py
from app import app
from database import db

with app.app_context():
    try:
        db.engine.connect()
        print("✅ PostgreSQL connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
```

Run: `python test_db.py`
