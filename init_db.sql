-- =============================================================================
-- Flashcard Learning System — Database Initialisation Script
-- =============================================================================
-- Runs automatically when the PostgreSQL Docker container starts for the
-- first time (mounted via docker-compose volumes).
--
-- NOTE: Tables are created by Alembic migrations (run via the backend).
--       This script only sets up extensions and DB-level settings that
--       must exist before Alembic runs.
--
-- After a fresh container start, run:
--   ./repopulate_db.sh   — to run migrations, create admin user, and seed configs
-- =============================================================================

-- Ensure UTF-8 encoding
ALTER DATABASE flashcard_db SET client_encoding TO 'utf8';

-- Required for UUID primary keys (gen_random_uuid() used throughout models)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Useful for full-text search (future use)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- Verification
-- =============================================================================
DO $$
DECLARE
    ext_count INT;
BEGIN
    SELECT COUNT(*) INTO ext_count
    FROM pg_extension
    WHERE extname IN ('uuid-ossp', 'pgcrypto', 'pg_trgm');

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Flashcard DB initialised successfully';
    RAISE NOTICE 'Extensions loaded: % / 3', ext_count;
    RAISE NOTICE 'Next step: run Alembic migrations via repopulate_db.sh';
    RAISE NOTICE '============================================================';
END $$;
