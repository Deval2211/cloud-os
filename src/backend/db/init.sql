-- Cloud OS Database Initialization Script
-- This script is automatically run when the PostgreSQL container starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set default timezone
SET timezone = 'UTC';

-- Create extensions for time-series data
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

PRINT 'Database initialized successfully';
