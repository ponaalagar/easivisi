-- EasiVisi Complete Database Schema (PostgreSQL)
-- Run this if you prefer SQL DDL instead of SQLAlchemy auto-creation

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    full_name VARCHAR(150),
    avatar_url VARCHAR(255),
    bio TEXT,
    
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    reset_token VARCHAR(100) UNIQUE,
    reset_token_expires TIMESTAMP,
    api_key VARCHAR(64) UNIQUE
);

CREATE INDEX ix_users_username ON users(username);
CREATE INDEX ix_users_email ON users(email);

-- ============================================================================
-- DATASETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_public BOOLEAN DEFAULT FALSE,
    
    total_images INTEGER DEFAULT 0,
    train_images INTEGER DEFAULT 0,
    val_images INTEGER DEFAULT 0,
    num_classes INTEGER DEFAULT 0,
    classes JSONB,
    
    dataset_path VARCHAR(500),
    yaml_path VARCHAR(500),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified_by INTEGER REFERENCES users(id)
);

CREATE INDEX ix_datasets_name ON datasets(name);
CREATE INDEX ix_datasets_owner_created ON datasets(owner_id, created_at);

-- ============================================================================
-- DATASET COLLABORATORS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS dataset_collaborators (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(20) DEFAULT 'view',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER REFERENCES users(id),
    
    CONSTRAINT unique_dataset_user UNIQUE (dataset_id, user_id)
);

-- ============================================================================
-- TRAINING RUNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(100) NOT NULL,
    run_id VARCHAR(50) UNIQUE NOT NULL,
    
    dataset_id INTEGER NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    model_name VARCHAR(50),
    epochs INTEGER,
    batch_size INTEGER,
    img_size INTEGER,
    device VARCHAR(20),
    
    status VARCHAR(20),
    progress FLOAT DEFAULT 0.0,
    
    final_map FLOAT,
    final_map50 FLOAT,
    final_loss FLOAT,
    training_time INTEGER,
    
    weights_path VARCHAR(500),
    results_path VARCHAR(500),
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_training_runs_run_id ON training_runs(run_id);
CREATE INDEX ix_training_runs_run_name ON training_runs(run_name);
CREATE INDEX ix_training_runs_creator_started ON training_runs(creator_id, started_at);

-- ============================================================================
-- MODEL EXPORTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_exports (
    id SERIAL PRIMARY KEY,
    training_run_id INTEGER NOT NULL REFERENCES training_runs(id) ON DELETE CASCADE,
    
    format VARCHAR(20) NOT NULL,
    export_path VARCHAR(500),
    file_size BIGINT,
    
    exported_by INTEGER REFERENCES users(id),
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ACTIVITY LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_activity_logs_created_at ON activity_logs(created_at);
CREATE INDEX ix_activity_logs_user_created ON activity_logs(user_id, created_at);

-- ============================================================================
-- TRAINING METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS training_metrics (
    id SERIAL PRIMARY KEY,
    training_run_id INTEGER NOT NULL REFERENCES training_runs(id) ON DELETE CASCADE,
    
    epoch INTEGER,
    train_loss FLOAT,
    val_loss FLOAT,
    map50 FLOAT,
    map FLOAT,
    precision FLOAT,
    recall FLOAT,
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_training_epoch UNIQUE (training_run_id, epoch)
);

-- ============================================================================
-- INSERT DEFAULT ADMIN USER
-- ============================================================================
-- Password: Admin@123 (hashed with pbkdf2:sha256)
INSERT INTO users (username, email, password_hash, full_name, role, is_active, is_verified)
VALUES (
    'admin',
    'admin@easivisi.local',
    'pbkdf2:sha256:600000$generated$hash',  -- Replace with actual hash
    'System Administrator',
    'admin',
    TRUE,
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- USEFUL QUERIES
-- ============================================================================

-- View all users
-- SELECT id, username, email, role, created_at FROM users;

-- View user datasets
-- SELECT d.name, d.total_images, d.created_at, u.username as owner
-- FROM datasets d JOIN users u ON d.owner_id = u.id;

-- View training runs with results
-- SELECT tr.run_name, tr.status, tr.final_map, d.name as dataset, u.username as creator
-- FROM training_runs tr
-- JOIN datasets d ON tr.dataset_id = d.id
-- JOIN users u ON tr.creator_id = u.id
-- ORDER BY tr.created_at DESC;
