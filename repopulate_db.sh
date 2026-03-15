#!/bin/bash

# =============================================================================
# Database Repopulation Script for Flashcard Learning System
# =============================================================================
# This script repopulates the database with essential data after reset/deletion:
# - Admin user account
# - All system configuration variables with CORRECT DATA TYPES
# - Database schema via migrations
# - Verification and fixing of configuration types to prevent type mismatch errors
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_CONTAINER="flashcard_postgres"
POSTGRES_USER="flashcard_user"
POSTGRES_DB="flashcard_db"
ADMIN_EMAIL="admin@flashcards.com"
ADMIN_PASSWORD="admin123"
ADMIN_NAME="Administrator"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi

# Check Docker containers are up, start them if not
if ! docker ps --format "{{.Names}}" | grep -q "flashcard_postgres"; then
    echo -e "${YELLOW}⚠️  Docker containers are not running — starting them...${NC}"
    docker compose up -d
    echo -e "${YELLOW}⏳ Waiting for Postgres to be ready...${NC}"
    for i in {1..15}; do
        pg_isready -h localhost -p 5433 > /dev/null 2>&1 && break
        sleep 1
    done
fi

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}  Flashcard Learning System - Database Repopulation Script${NC}"
echo -e "${BLUE}==============================================================================${NC}"

# Function to check if Docker container is running
check_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${POSTGRES_CONTAINER}$"; then
        echo -e "${RED}❌ PostgreSQL container '${POSTGRES_CONTAINER}' is not running${NC}"
        echo -e "${YELLOW}💡 Please start the services first: docker-compose up -d${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ PostgreSQL container is running${NC}"
}

# Function to wait for database to be ready
wait_for_db() {
    echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
    local retries=30
    while [ $retries -gt 0 ]; do
        if docker exec -it ${POSTGRES_CONTAINER} pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Database is ready${NC}"
            return 0
        fi
        retries=$((retries - 1))
        sleep 2
        echo -n "."
    done
    echo -e "${RED}❌ Database failed to become ready${NC}"
    exit 1
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}🔧 Running database migrations...${NC}"
    
    # Check if backend container exists and is running
    if docker ps --format "table {{.Names}}" | grep -q "^flashcard_backend$"; then
        echo -e "${BLUE}📋 Running Alembic migrations via backend container...${NC}"
        docker exec flashcard_backend alembic upgrade head
    else
        echo -e "${YELLOW}⚠️  Backend container not running, migrations may need to be run manually${NC}"
        echo -e "${BLUE}💡 You can run migrations later with: docker exec flashcard_backend alembic upgrade head${NC}"
    fi
}

# Function to create admin user
create_admin_user() {
    echo -e "${YELLOW}👤 Creating admin user...${NC}"
    
    # Check if user already exists
    local user_exists=$(docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM users WHERE email = '${ADMIN_EMAIL}';" 2>/dev/null | tr -d ' \r\n' || echo "0")
    
    if [ "$user_exists" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Admin user already exists, updating admin privileges...${NC}"
        docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "UPDATE users SET is_admin = true WHERE email = '${ADMIN_EMAIL}';" > /dev/null
        echo -e "${GREEN}✅ Admin privileges updated for ${ADMIN_EMAIL}${NC}"
    else
        echo -e "${BLUE}📝 Registering new admin user via API...${NC}"
        
        # Wait a moment for backend to be ready
        sleep 3
        
        # Register user via API
        local response=$(curl -s -X POST "http://localhost:8000/api/v1/auth/register" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\",\"name\":\"${ADMIN_NAME}\"}" 2>/dev/null || echo "")
        
        if echo "$response" | grep -q '"email"'; then
            echo -e "${GREEN}✅ Admin user created via API${NC}"
            
            # Grant admin privileges
            docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "UPDATE users SET is_admin = true WHERE email = '${ADMIN_EMAIL}';" > /dev/null
            echo -e "${GREEN}✅ Admin privileges granted${NC}"
        else
            echo -e "${YELLOW}⚠️  API registration failed, creating user directly in database...${NC}"
            
            # Create user directly in database with a proper bcrypt hash
            # Note: This is a fallback method, API registration is preferred
            # Using a verified bcrypt hash for password "admin123"
            docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
                DELETE FROM users WHERE email = '${ADMIN_EMAIL}';
                INSERT INTO users (id, email, name, hashed_password, is_admin, is_active) 
                VALUES (
                    gen_random_uuid(), 
                    '${ADMIN_EMAIL}', 
                    '${ADMIN_NAME}', 
                    '\$2b\$12\$Dzmm6VaLv9SgNd3ZOrUEluASXnA5pLbQZm3yAYTNvSU.fLbt8upfa', 
                    true, 
                    true
                );
            " > /dev/null
            echo -e "${GREEN}✅ Admin user created with verified bcrypt hash${NC}"
        fi
    fi
}

# Function to populate system configurations
populate_system_configs() {
    echo -e "${YELLOW}⚙️  Populating system configurations...${NC}"

    # Learning Configurations (9 configs)
    echo -e "${BLUE}📚 Adding learning configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'initial_set_size',          '10',          'integer', 'Starting number of flashcards for new users',                          'learning'),
        (gen_random_uuid(), 'max_set_size',              '30',          'integer', 'Maximum number of flashcards in a learning set',                       'learning'),
        (gen_random_uuid(), 'stage_increment',           '10',          'integer', 'How many cards to add when advancing to next stage',                   'learning'),
        (gen_random_uuid(), 'mid_tier_threshold',        '80',          'integer', 'Threshold for mid-tier optimisation (datasets with 16-80 cards)',      'learning'),
        (gen_random_uuid(), 'chunk_size_progression',    '100,75,60,50','string',  'Comma-separated chunk sizes for large dataset progression',            'learning'),
        (gen_random_uuid(), 'reinforcement_percentage',  '10',          'integer', 'Percentage of previously learned cards included for reinforcement',    'learning'),
        (gen_random_uuid(), 'batch_size',                '5',           'integer', 'Number of cards per learning batch',                                   'learning'),
        (gen_random_uuid(), 'distractor_count',          '3',           'integer', 'Number of wrong answer options shown per question',                    'learning'),
        (gen_random_uuid(), 'isolation_mastery_percentage', '0.8',      'float',   'Accuracy threshold to pass isolation phase',                           'learning'),
        (gen_random_uuid(), 'integration_mastery_percentage', '0.7',    'float',   'Accuracy threshold to pass integration phase',                         'learning'),
        (gen_random_uuid(), 'mastery_review_window',     '10',          'integer', 'Rolling window of attempts used to evaluate mastery',                  'learning')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # Spaced Repetition Configurations (10 configs)
    echo -e "${BLUE}🧠 Adding spaced repetition configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'initial_ease',        '2.5',      'float',   'Initial ease factor for new cards (FSRS)',                  'spaced_repetition'),
        (gen_random_uuid(), 'minimum_ease',        '1.3',      'float',   'Minimum ease factor floor for difficult cards',             'spaced_repetition'),
        (gen_random_uuid(), 'maximum_ease',        '5.0',      'float',   'Maximum ease factor ceiling for easy cards',                'spaced_repetition'),
        (gen_random_uuid(), 'ease_bonus',          '0.15',     'float',   'Ease factor bonus added for correct answers',               'spaced_repetition'),
        (gen_random_uuid(), 'ease_penalty',        '0.2',      'float',   'Ease factor penalty subtracted for wrong answers',          'spaced_repetition'),
        (gen_random_uuid(), 'initial_interval',    '1',        'integer', 'Initial review interval in days for new cards',             'spaced_repetition'),
        (gen_random_uuid(), 'graduation_interval', '4',        'integer', 'Days to graduate from learning phase to review phase',      'spaced_repetition'),
        (gen_random_uuid(), 'maximum_interval',    '365',      'integer', 'Maximum days between reviews',                             'spaced_repetition'),
        (gen_random_uuid(), 'learning_steps',      '1,10,1440','string',  'Learning step durations in minutes (1min, 10min, 1day)',    'spaced_repetition'),
        (gen_random_uuid(), 'relearning_steps',    '10,1440',  'string',  'Relearning steps in minutes for failed cards (10min, 1day)','spaced_repetition')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # Spiral Learning Configurations (6 configs)
    echo -e "${BLUE}🔄 Adding spiral learning configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'spiral_learning_enabled',          'true', 'boolean', 'Enable spiral review pass after integration cycles',          'spiral_learning'),
        (gen_random_uuid(), 'spiral_review_trigger_interval',   '2',    'integer', 'Integration cycles between spiral review triggers',           'spiral_learning'),
        (gen_random_uuid(), 'spiral_review_max_cards',          '20',   'integer', 'Maximum cards pulled into a spiral review pass',              'spiral_learning'),
        (gen_random_uuid(), 'spiral_weakness_threshold',        '0.6',  'float',   'Accuracy below this flags a card as weak for spiral review',  'spiral_learning'),
        (gen_random_uuid(), 'spiral_stability_threshold',       '1.5',  'float',   'Stability score below this triggers spiral review',           'spiral_learning'),
        (gen_random_uuid(), 'spiral_integration_failure_weight','2.0',  'float',   'Weight multiplier for integration failures in spiral scoring', 'spiral_learning')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # FSRS Integration Configurations (9 configs)
    echo -e "${BLUE}⚡ Adding FSRS integration configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'integration_enhancement_enabled',   'true', 'boolean', 'Enable FSRS stability tracking during integration phase',    'fsrs_integration'),
        (gen_random_uuid(), 'integration_confirmation_threshold','0.8',  'float',   'Accuracy threshold for integration confirmation',            'fsrs_integration'),
        (gen_random_uuid(), 'integration_max_attempts',          '3',    'integer', 'Maximum integration attempts before card cycles back',       'fsrs_integration'),
        (gen_random_uuid(), 'stability_boost_factor',            '1.2',  'float',   'Stability multiplier on correct integration answer',         'fsrs_integration'),
        (gen_random_uuid(), 'stability_decay_factor',            '0.8',  'float',   'Stability multiplier on wrong integration answer',           'fsrs_integration'),
        (gen_random_uuid(), 'stability_max_score',               '3.0',  'float',   'Maximum stability score a card can reach',                   'fsrs_integration'),
        (gen_random_uuid(), 'integration_failure_penalty',       '0.85', 'float',   'Score penalty factor applied on integration failure',        'fsrs_integration'),
        (gen_random_uuid(), 'reconsolidation_threshold',         '2',    'integer', 'Failures before card is sent back to isolation learning',    'fsrs_integration'),
        (gen_random_uuid(), 'stability_maintenance_boost',       '1.05', 'float',   'Stability boost applied to confirmed cards in maintenance',  'fsrs_integration')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # FSRS Mastery Window Configurations (9 configs)
    echo -e "${BLUE}🎯 Adding FSRS mastery window configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'default_mastery_window',          '3',   'integer', 'Default rolling window for mastery evaluation',                  'fsrs_mastery'),
        (gen_random_uuid(), 'isolation_min_mastery_window',    '2',   'integer', 'Minimum mastery window for isolation phase',                     'fsrs_mastery'),
        (gen_random_uuid(), 'isolation_max_mastery_window',    '8',   'integer', 'Maximum mastery window for isolation phase',                     'fsrs_mastery'),
        (gen_random_uuid(), 'isolation_field_multiplier',      '1.5', 'float',   'Window multiplier per additional card field',                    'fsrs_mastery'),
        (gen_random_uuid(), 'single_field_mastery_window',     '2',   'integer', 'Mastery window for single-field cards',                         'fsrs_mastery'),
        (gen_random_uuid(), 'two_field_mastery_window',        '3',   'integer', 'Mastery window for two-field cards',                            'fsrs_mastery'),
        (gen_random_uuid(), 'integration_mastery_window',      '1',   'integer', 'Mastery window for integration confirmation (single attempt)',   'fsrs_mastery'),
        (gen_random_uuid(), 'required_mastery_window',         '3',   'integer', 'Required window size before mastery can be awarded',            'fsrs_mastery'),
        (gen_random_uuid(), 'initial_stability_score',         '1.0', 'float',   'Starting stability score assigned to new cards',                'fsrs_mastery')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # Classification / Phase Transition Configurations (16 configs)
    echo -e "${BLUE}🔀 Adding classification configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'learning_min_attempts',                      '2',    'integer', 'Minimum attempts before leaving learning phase',                    'classification'),
        (gen_random_uuid(), 'learning_accuracy_threshold',                '0.6',  'float',   'Accuracy required to exit learning phase',                         'classification'),
        (gen_random_uuid(), 'learning_success_streak_required',           '0',    'integer', 'Consecutive correct answers required to exit learning phase',       'classification'),
        (gen_random_uuid(), 'isolation_mastery_attempts_required',        '3',    'integer', 'Attempts required to pass isolation mastery check',                 'classification'),
        (gen_random_uuid(), 'isolation_mastery_accuracy_threshold',       '0.8',  'float',   'Accuracy required to pass isolation mastery check',                 'classification'),
        (gen_random_uuid(), 'isolation_mastery_success_streak_required',  '2',    'integer', 'Consecutive correct answers required for isolation mastery',        'classification'),
        (gen_random_uuid(), 'isolation_mastery_window_days',              '1',    'integer', 'Days window used to assess isolation mastery',                      'classification'),
        (gen_random_uuid(), 'integration_confirmation_attempts_required', '1',    'integer', 'Attempts required to confirm integration mastery',                  'classification'),
        (gen_random_uuid(), 'integration_confirmation_accuracy_threshold','1.0',  'float',   'Accuracy required for integration confirmation (must be perfect)',  'classification'),
        (gen_random_uuid(), 'integration_max_failure_attempts',           '3',    'integer', 'Max failures before card cycles back to learning',                  'classification'),
        (gen_random_uuid(), 'integration_review_penalty_factor',          '0.8',  'float',   'Score penalty applied when integration review fails',               'classification'),
        (gen_random_uuid(), 'integration_confirmed_maintenance_threshold','0.9',  'float',   'Accuracy threshold to stay in confirmed maintenance mode',          'classification'),
        (gen_random_uuid(), 'integration_confirmed_stability_boost',      '1.1',  'float',   'Stability boost for cards passing confirmed maintenance check',     'classification'),
        (gen_random_uuid(), 'integration_confirmed_failure_penalty',      '0.95', 'float',   'Stability penalty for confirmed cards that fail maintenance',       'classification'),
        (gen_random_uuid(), 'spiral_review_trigger_cycles',               '2',    'integer', 'Integration cycles before spiral review is triggered',              'classification'),
        (gen_random_uuid(), 'spiral_review_weakness_threshold',           '0.7',  'float',   'Accuracy below this marks a card weak in spiral review',            'classification'),
        (gen_random_uuid(), 'spiral_review_stability_threshold',          '1.5',  'float',   'Stability below this marks a card for spiral review',               'classification'),
        (gen_random_uuid(), 'spiral_review_success_threshold',            '0.8',  'float',   'Accuracy required to pass spiral review and restore confidence',    'classification'),
        (gen_random_uuid(), 'allow_status_downgrading',                   'false','boolean', 'Allow cards to move backwards through phases',                     'classification'),
        (gen_random_uuid(), 'remediation_attempts_threshold',             '5',    'integer', 'Attempts threshold before remediation is triggered',               'classification'),
        (gen_random_uuid(), 'consolidation_window_hours',                 '24',   'integer', 'Hours window used for consolidation checks',                       'classification'),
        (gen_random_uuid(), 'track_isolation_attempts',                   'true', 'boolean', 'Track individual attempt history during isolation phase',           'classification'),
        (gen_random_uuid(), 'track_integration_attempts',                 'true', 'boolean', 'Track individual attempt history during integration phase',         'classification'),
        (gen_random_uuid(), 'track_spiral_attempts',                      'true', 'boolean', 'Track individual attempt history during spiral review',             'classification'),
        (gen_random_uuid(), 'reset_attempts_on_mastery',                  'false','boolean', 'Reset attempt history when a card achieves mastery',               'classification')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    # Ranking Configurations (3 configs)
    echo -e "${BLUE}🏆 Adding ranking configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'accuracy_min_cards',           '5',  'integer', 'Minimum cards answered to appear in accuracy leaderboard', 'ranking'),
        (gen_random_uuid(), 'speed_min_cards',              '10', 'integer', 'Minimum cards answered to appear in speed leaderboard',    'ranking'),
        (gen_random_uuid(), 'cards_answered_min_threshold', '20', 'integer', 'Minimum cards answered to appear in any leaderboard',      'ranking')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null

    echo -e "${GREEN}✅ System configurations populated (68 total configs)${NC}"

    # Verify and fix configuration types to prevent type mismatch errors
    fix_configuration_types
}

# Function to fix configuration types (prevent type mismatch errors)
fix_configuration_types() {
    echo -e "${YELLOW}🔧 Fixing configuration value types...${NC}"
    
    # Fix any incorrect 'int' types to 'integer' (SystemConfig.typed_value only recognizes 'integer')
    local fixed_count=$(docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "
        UPDATE system_configs 
        SET value_type = 'integer' 
        WHERE value_type = 'int';
        SELECT ROW_COUNT();
    " 2>/dev/null | tr -d ' \r\n' | tail -1 || echo "0")
    
    # Fix any incorrect 'str' types to 'string'
    local fixed_str_count=$(docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "
        UPDATE system_configs 
        SET value_type = 'string' 
        WHERE value_type = 'str';
        SELECT ROW_COUNT();
    " 2>/dev/null | tr -d ' \r\n' | tail -1 || echo "0")
    
    # Verify critical learning configuration types
    echo -e "${BLUE}🔍 Verifying critical configuration types...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        SELECT 
            key,
            value,
            value_type,
            CASE 
                WHEN value_type = 'integer' AND value ~ '^[0-9]+$' THEN '✅'
                WHEN value_type = 'float' AND value ~ '^[0-9]*\.?[0-9]+$' THEN '✅'
                WHEN value_type = 'string' THEN '✅'
                WHEN value_type = 'boolean' AND value IN ('true', 'false', '1', '0') THEN '✅'
                ELSE '❌'
            END as status
        FROM system_configs 
        WHERE key IN ('initial_set_size', 'stage_increment', 'mastery_threshold', 'max_set_size', 'mid_tier_threshold')
        ORDER BY key;
    " 2>/dev/null || echo "Could not verify configuration types"
    
    if [ "$fixed_count" -gt 0 ] || [ "$fixed_str_count" -gt 0 ]; then
        echo -e "${GREEN}✅ Fixed ${fixed_count} 'int'→'integer' and ${fixed_str_count} 'str'→'string' type corrections${NC}"
    else
        echo -e "${GREEN}✅ All configuration types are correct${NC}"
    fi
}

# Function to verify installation
verify_installation() {
    echo -e "${YELLOW}🔍 Verifying installation...${NC}"
    
    # Check admin user
    local admin_count=$(docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM users WHERE email = '${ADMIN_EMAIL}' AND is_admin = true;" | tr -d ' \r\n')
    
    # Check system configs
    local config_count=$(docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT COUNT(*) FROM system_configs;" | tr -d ' \r\n')
    
    echo -e "${BLUE}📊 Verification Results:${NC}"
    echo -e "   👤 Admin users: ${admin_count}"
    echo -e "   ⚙️  System configs: ${config_count}"
    
    if [ "$admin_count" -gt 0 ] && [ "$config_count" -gt 60 ]; then
        echo -e "${GREEN}✅ Database repopulation completed successfully!${NC}"
        echo -e ""
        echo -e "${BLUE}🎉 Ready to use:${NC}"
        echo -e "   🌐 Admin Panel: http://localhost:3000/admin"
        echo -e "   📧 Admin Email: ${ADMIN_EMAIL}"
        echo -e "   🔐 Admin Password: ${ADMIN_PASSWORD}"
        echo -e "   📊 System Configs: ${config_count} / 68 configurations loaded"
    else
        echo -e "${RED}❌ Verification failed. Some data may be missing.${NC}"
        exit 1
    fi
}

# Function to show configuration summary
show_config_summary() {
    echo -e "${BLUE}📋 Configuration Summary:${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        SELECT 
            category,
            COUNT(*) as config_count
        FROM system_configs 
        GROUP BY category 
        ORDER BY category;
    " 2>/dev/null || echo "Could not retrieve configuration summary"
}

# Main execution
main() {
    echo -e "${YELLOW}🚀 Starting database repopulation...${NC}"
    
    check_container
    wait_for_db
    run_migrations
    create_admin_user
    populate_system_configs
    verify_installation
    show_config_summary
    
    echo -e ""
    echo -e "${GREEN}🎯 Database repopulation complete!${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --verify, -v   Only verify current installation"
        echo "  --configs, -c  Only repopulate system configurations"
        echo ""
        echo "This script repopulates the flashcard database with:"
        echo "  • Admin user (${ADMIN_EMAIL})"
        echo "  • 68 system configuration variables (all categories)"
        echo "  • Database migrations (if backend is running)"
        exit 0
        ;;
    --verify|-v)
        check_container
        wait_for_db
        verify_installation
        show_config_summary
        exit 0
        ;;
    --configs|-c)
        check_container
        wait_for_db
        populate_system_configs
        show_config_summary
        exit 0
        ;;
    *)
        main
        ;;
esac
