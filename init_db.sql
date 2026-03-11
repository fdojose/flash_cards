-- Initialize flashcard_db with proper encoding and extensions
-- This script runs when the PostgreSQL container starts for the first time

-- Ensure UTF8 encoding
ALTER DATABASE flashcard_db SET client_encoding TO 'utf8';

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create initial schema structure (basic tables will be created by Alembic later)
-- This is just to ensure the database is ready

-- Log successful initialization
DO $$ 
BEGIN 
    RAISE NOTICE 'Flashcard database initialized successfully';
END $$;
