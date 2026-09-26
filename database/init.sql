-- ===========================================
-- SCM Procurement Control Tower
-- Database Initialization
-- ===========================================
-- This script runs once when the PostgreSQL container first starts.
-- All table creation is managed by Alembic migrations.

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Confirm initialization
DO $$
BEGIN
    RAISE NOTICE 'SCM Procurement database initialized successfully.';
END $$;
