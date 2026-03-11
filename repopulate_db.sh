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
    
    # Learning Algorithm Configurations (7 configs)
    echo -e "${BLUE}📚 Adding learning algorithm configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'initial_set_size', '10', 'integer', 'Starting number of flashcards for new users', 'learning'),
        (gen_random_uuid(), 'mastery_threshold', '3', 'integer', 'Number of consecutive correct answers needed to mark an element as mastered', 'learning'),
        (gen_random_uuid(), 'max_set_size', '30', 'integer', 'Maximum number of flashcards in a learning set', 'learning'),
        (gen_random_uuid(), 'stage_increment', '10', 'integer', 'How many cards to add when advancing to next stage', 'learning'),
        (gen_random_uuid(), 'mid_tier_threshold', '80', 'integer', 'Threshold for mid-tier optimization (datasets with 16-80 cards)', 'learning'),
        (gen_random_uuid(), 'chunk_size_progression', '100,75,60,50', 'string', 'Comma-separated list of chunk sizes for large dataset progression', 'learning'),
        (gen_random_uuid(), 'reinforcement_percentage', '10', 'integer', 'Percentage of previously learned cards to include for reinforcement', 'learning')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null
    
    # Spaced Repetition Configurations (10 configs)
    echo -e "${BLUE}🧠 Adding spaced repetition configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'initial_ease', '2.5', 'float', 'Initial ease factor for new cards in spaced repetition (SM-2 algorithm)', 'spaced_repetition'),
        (gen_random_uuid(), 'minimum_ease', '1.3', 'float', 'Minimum ease factor (floor value for difficult cards)', 'spaced_repetition'),
        (gen_random_uuid(), 'maximum_ease', '5.0', 'float', 'Maximum ease factor (ceiling value for easy cards)', 'spaced_repetition'),
        (gen_random_uuid(), 'ease_bonus', '0.15', 'float', 'Ease factor bonus added for correct answers', 'spaced_repetition'),
        (gen_random_uuid(), 'ease_penalty', '0.2', 'float', 'Ease factor penalty subtracted for wrong answers', 'spaced_repetition'),
        (gen_random_uuid(), 'initial_interval', '1', 'integer', 'Initial review interval in days for new cards', 'spaced_repetition'),
        (gen_random_uuid(), 'graduation_interval', '4', 'integer', 'Days to graduate from learning phase to review phase', 'spaced_repetition'),
        (gen_random_uuid(), 'maximum_interval', '365', 'integer', 'Maximum days between reviews', 'spaced_repetition'),
        (gen_random_uuid(), 'learning_steps', '1,10,1440', 'string', 'Learning steps in minutes (comma-separated: 1min, 10min, 1day)', 'spaced_repetition'),
        (gen_random_uuid(), 'relearning_steps', '10,1440', 'string', 'Relearning steps in minutes for failed cards (10min, 1day)', 'spaced_repetition')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null
    
    # Ranking Configurations (3 configs)
    echo -e "${BLUE}🏆 Adding ranking configurations...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "
        INSERT INTO system_configs (id, key, value, value_type, description, category) VALUES
        (gen_random_uuid(), 'accuracy_min_cards', '5', 'integer', 'Minimum cards answered for accuracy ranking', 'ranking'),
        (gen_random_uuid(), 'speed_min_cards', '10', 'integer', 'Minimum cards answered for speed ranking', 'ranking'),
        (gen_random_uuid(), 'cards_answered_min_threshold', '20', 'integer', 'Minimum cards answered for leaderboard appearance', 'ranking')
        ON CONFLICT (key) DO NOTHING;
    " > /dev/null
    
    echo -e "${GREEN}✅ System configurations populated (20 total configs)${NC}"
    
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
    
    if [ "$admin_count" -gt 0 ] && [ "$config_count" -gt 15 ]; then
        echo -e "${GREEN}✅ Database repopulation completed successfully!${NC}"
        echo -e ""
        echo -e "${BLUE}🎉 Ready to use:${NC}"
        echo -e "   🌐 Admin Panel: http://localhost:3000/admin"
        echo -e "   📧 Admin Email: ${ADMIN_EMAIL}"
        echo -e "   🔐 Admin Password: ${ADMIN_PASSWORD}"
        echo -e "   📊 System Configs: ${config_count} configurations available"
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
        echo "  • 17 system configuration variables"
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
