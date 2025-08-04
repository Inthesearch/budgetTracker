-- Budget Tracker Database Setup Script
-- Run this script as a PostgreSQL superuser (like postgres)

-- Create database
CREATE DATABASE budget_tracker;

-- Connect to the database
\c budget_tracker;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create a dedicated user for the application (optional but recommended for production)
-- CREATE USER budget_tracker_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE budget_tracker TO budget_tracker_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO budget_tracker_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO budget_tracker_user;

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (these will be created by SQLAlchemy, but you can add custom ones)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date DESC);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_category ON transactions(category_id) WHERE category_id IS NOT NULL;
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_type ON transactions(type);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categories_user ON categories(user_id, is_active);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sub_categories_user_category ON sub_categories(user_id, category_id, is_active);

-- Verify database creation
SELECT current_database(), current_user, version();

-- Show created extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto'); 