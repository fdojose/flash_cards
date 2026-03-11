#!/bin/bash

# FSRS Integration Rollback Script
# 
# Comprehensive rollback procedures for FSRS integration system
# Supports rollback to pre-FSRS state with data preservation options

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}"
BACKUP_DIR="${SCRIPT_DIR}/backups"
LOG_FILE="${SCRIPT_DIR}/logs/fsrs_rollback_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"

show_usage() {
    cat << EOF
FSRS Integration Rollback Script

Usage: $0 [OPTIONS]

Options:
    --full              Full rollback (database + code)
    --database-only     Rollback database changes only
    --code-only         Rollback code changes only
    --preserve-data     Preserve FSRS integration data during rollback
    --backup-name NAME  Use specific backup (default: latest)
    --dry-run          Show what would be done without executing
    --force            Skip confirmation prompts
    -h, --help         Show this help message

Examples:
    $0 --full                    # Full rollback with confirmation
    $0 --database-only --force   # Quick database rollback
    $0 --dry-run                 # Preview rollback actions
    $0 --preserve-data --full    # Rollback but keep integration data

EOF
}

# Parse command line arguments
ROLLBACK_TYPE=""
PRESERVE_DATA=false
BACKUP_NAME=""
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            ROLLBACK_TYPE="full"
            shift
            ;;
        --database-only)
            ROLLBACK_TYPE="database"
            shift
            ;;
        --code-only)
            ROLLBACK_TYPE="code"
            shift
            ;;
        --preserve-data)
            PRESERVE_DATA=true
            shift
            ;;
        --backup-name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Default to full rollback if not specified
if [[ -z "$ROLLBACK_TYPE" ]]; then
    ROLLBACK_TYPE="full"
fi

log "Starting FSRS Integration Rollback"
log "Rollback Type: $ROLLBACK_TYPE"
log "Preserve Data: $PRESERVE_DATA"
log "Dry Run: $DRY_RUN"

# Validation functions
check_prerequisites() {
    log "Checking rollback prerequisites..."
    
    # Check if backup directory exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi
    
    # Find latest backup if no specific backup specified
    if [[ -z "$BACKUP_NAME" ]]; then
        BACKUP_NAME=$(ls -t "$BACKUP_DIR"/*.sql 2>/dev/null | head -1 | xargs basename -s .sql || echo "")
        if [[ -z "$BACKUP_NAME" ]]; then
            log_error "No database backups found in $BACKUP_DIR"
            return 1
        fi
        log "Using latest backup: $BACKUP_NAME"
    fi
    
    # Check if backup file exists
    if [[ ! -f "$BACKUP_DIR/${BACKUP_NAME}.sql" ]]; then
        log_error "Backup file not found: $BACKUP_DIR/${BACKUP_NAME}.sql"
        return 1
    fi
    
    # Check if Docker is running (if using Docker)
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        log "Docker is available and running"
    else
        log_warning "Docker not available - assuming direct database connection"
    fi
    
    log_success "Prerequisites check completed"
}

# Backup current state before rollback
create_rollback_backup() {
    log "Creating pre-rollback backup..."
    
    local rollback_backup_name="pre_rollback_$(date +%Y%m%d_%H%M%S)"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would create backup: ${rollback_backup_name}.sql"
        return 0
    fi
    
    # Database backup
    if command -v docker &> /dev/null && docker ps | grep -q postgres; then
        docker exec flashcard-db pg_dump -U postgres flashcard_db > "$BACKUP_DIR/${rollback_backup_name}.sql" 2>/dev/null
    else
        # Assume local postgres
        pg_dump flashcard_db > "$BACKUP_DIR/${rollback_backup_name}.sql" 2>/dev/null
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Pre-rollback backup created: ${rollback_backup_name}.sql"
    else
        log_warning "Failed to create pre-rollback backup - continuing anyway"
    fi
}

# Database rollback functions
rollback_database() {
    log "Starting database rollback..."
    
    local backup_file="$BACKUP_DIR/${BACKUP_NAME}.sql"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would restore database from: $backup_file"
        log "[DRY RUN] Would remove FSRS integration fields if preserve-data is false"
        return 0
    fi
    
    # Stop application to prevent database access during rollback
    log "Stopping application services..."
    if command -v docker-compose &> /dev/null && [[ -f "docker-compose.yml" ]]; then
        docker-compose stop backend || log_warning "Could not stop backend service"
    fi
    
    # Restore database
    log "Restoring database from backup..."
    if command -v docker &> /dev/null && docker ps | grep -q postgres; then
        # Docker postgres
        docker exec -i flashcard-db psql -U postgres -d flashcard_db < "$backup_file"
    else
        # Local postgres
        psql flashcard_db < "$backup_file"
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Database restored from backup"
    else
        log_error "Failed to restore database"
        return 1
    fi
    
    # Handle FSRS integration data
    if [[ "$PRESERVE_DATA" == "false" ]]; then
        log "Removing FSRS integration fields..."
        
        # Remove FSRS fields from user_element_reviews
        local remove_fields_sql="
        ALTER TABLE user_element_reviews 
        DROP COLUMN IF EXISTS integration_confirmed,
        DROP COLUMN IF EXISTS integration_attempts,
        DROP COLUMN IF EXISTS last_integration_attempt,
        DROP COLUMN IF EXISTS stability_score;
        
        -- Remove FSRS configuration entries
        DELETE FROM system_config WHERE key LIKE 'fsrs_%';
        "
        
        if command -v docker &> /dev/null && docker ps | grep -q postgres; then
            echo "$remove_fields_sql" | docker exec -i flashcard-db psql -U postgres -d flashcard_db
        else
            echo "$remove_fields_sql" | psql flashcard_db
        fi
        
        log_success "FSRS integration fields removed"
    else
        log_success "FSRS integration data preserved"
    fi
}

# Code rollback functions
rollback_code() {
    log "Starting code rollback..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would revert FSRS code changes"
        log "[DRY RUN] Would remove FSRS-specific files"
        log "[DRY RUN] Would restore original route files"
        return 0
    fi
    
    # Remove FSRS-specific files
    local fsrs_files=(
        "migrations/add_integration_tracking.py"
        "admin/fsrs_config.py"
        "tests/test_fsrs_integration.py"
        "tests/test_fsrs_api.py"
        "scripts/validate_fsrs_system.py"
        "scripts/run_fsrs_tests.py"
        "scripts/seed_fsrs_config.py"
        "fsrs_monitor.py"
        "fsrs_dashboard.py"
        "templates/fsrs_dashboard.html"
    )
    
    for file in "${fsrs_files[@]}"; do
        if [[ -f "$file" ]]; then
            log "Removing FSRS file: $file"
            rm "$file"
        fi
    done
    
    # Restore original route files from backup if available
    if [[ -f "$BACKUP_DIR/sessions_routes_backup.py" ]]; then
        log "Restoring original sessions routes..."
        cp "$BACKUP_DIR/sessions_routes_backup.py" "sessions/routes.py"
        log_success "Sessions routes restored"
    else
        log_warning "Original sessions routes backup not found - manual intervention may be required"
    fi
    
    if [[ -f "$BACKUP_DIR/admin_routes_backup.py" ]]; then
        log "Restoring original admin routes..."
        cp "$BACKUP_DIR/admin_routes_backup.py" "admin/routes.py"
        log_success "Admin routes restored"
    else
        log_warning "Original admin routes backup not found - manual intervention may be required"
    fi
    
    # Restore original model files
    if [[ -f "$BACKUP_DIR/models_backup.py" ]]; then
        log "Restoring original models..."
        cp "$BACKUP_DIR/models_backup.py" "models.py"
        log_success "Models restored"
    else
        log_warning "Original models backup not found - manual intervention may be required"
    fi
    
    log_success "Code rollback completed"
}

# System verification after rollback
verify_rollback() {
    log "Verifying rollback completion..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY RUN] Would verify system functionality"
        log "[DRY RUN] Would check database schema"
        log "[DRY RUN] Would test API endpoints"
        return 0
    fi
    
    # Start services
    log "Starting application services..."
    if command -v docker-compose &> /dev/null && [[ -f "docker-compose.yml" ]]; then
        docker-compose up -d backend
        sleep 10  # Wait for services to start
    fi
    
    # Check database schema
    log "Checking database schema..."
    local schema_check="SELECT column_name FROM information_schema.columns WHERE table_name = 'user_element_reviews' AND column_name IN ('integration_confirmed', 'stability_score');"
    
    local fsrs_columns=""
    if command -v docker &> /dev/null && docker ps | grep -q postgres; then
        fsrs_columns=$(echo "$schema_check" | docker exec -i flashcard-db psql -U postgres -d flashcard_db -t | xargs)
    else
        fsrs_columns=$(echo "$schema_check" | psql flashcard_db -t | xargs)
    fi
    
    if [[ "$PRESERVE_DATA" == "false" ]]; then
        if [[ -n "$fsrs_columns" ]]; then
            log_warning "FSRS columns still present after rollback: $fsrs_columns"
        else
            log_success "FSRS columns successfully removed"
        fi
    else
        if [[ -n "$fsrs_columns" ]]; then
            log_success "FSRS columns preserved as requested"
        else
            log_warning "FSRS columns missing - data may not be preserved"
        fi
    fi
    
    # Test basic API functionality
    log "Testing basic API functionality..."
    sleep 5  # Additional wait for backend
    
    if curl -s -f "http://localhost:8000/health" > /dev/null; then
        log_success "Backend API responding"
    else
        log_error "Backend API not responding - manual intervention required"
    fi
    
    log_success "Rollback verification completed"
}

# Confirmation prompt
confirm_rollback() {
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    
    echo
    log_warning "ROLLBACK CONFIRMATION REQUIRED"
    echo
    echo "  Rollback Type: $ROLLBACK_TYPE"
    echo "  Backup: $BACKUP_NAME"
    echo "  Preserve Data: $PRESERVE_DATA"
    echo "  Dry Run: $DRY_RUN"
    echo
    
    if [[ "$PRESERVE_DATA" == "false" ]]; then
        echo -e "${RED}⚠️  WARNING: All FSRS integration data will be permanently lost!${NC}"
        echo
    fi
    
    read -p "Do you want to proceed with the rollback? [y/N]: " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Rollback cancelled by user"
        exit 0
    fi
}

# Main rollback execution
main() {
    log "FSRS Integration Rollback Started"
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        exit 1
    fi
    
    # Confirm rollback
    confirm_rollback
    
    # Create backup before rollback
    create_rollback_backup
    
    # Execute rollback based on type
    case "$ROLLBACK_TYPE" in
        "full")
            log "Executing full rollback (database + code)..."
            rollback_database
            rollback_code
            ;;
        "database")
            log "Executing database rollback only..."
            rollback_database
            ;;
        "code")
            log "Executing code rollback only..."
            rollback_code
            ;;
        *)
            log_error "Unknown rollback type: $ROLLBACK_TYPE"
            exit 1
            ;;
    esac
    
    # Verify rollback
    verify_rollback
    
    log_success "FSRS Integration Rollback Completed Successfully"
    echo
    log "Rollback log saved to: $LOG_FILE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo
        log_warning "This was a DRY RUN - no actual changes were made"
        log "To execute the rollback, run the same command without --dry-run"
    fi
}

# Execute main function
main "$@"
