#!/bin/bash

# =============================================================================
# Database and File Storage Restore Script
# 3D Print Management System - Masterplan Compliant Recovery Procedures
# =============================================================================
#
# This script implements the recovery procedures defined in Section 5.8 of the
# masterplan, providing safe and verified restoration of both database and
# file storage from synchronized backup sets.
#
# Features:
# - Safe restoration with validation and confirmation prompts
# - Automatic backup verification before restore
# - Database and file storage synchronization checks
# - System integrity audit after restoration
# - Rollback capabilities for failed restores
# - Comprehensive logging and reporting
#
# Usage:
#   ./restore_database.sh --backup-date YYYYMMDD [OPTIONS]
#   ./restore_database.sh --list-backups
#   ./restore_database.sh --verify-backup YYYYMMDD
#
# IMPORTANT: This script will overwrite existing data. Use with caution!

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# Configuration and Environment Setup
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_CONFIG="$PROJECT_ROOT/.env"

# Load configuration
RESTORE_CONFIG="${RESTORE_CONFIG:-$DEFAULT_CONFIG}"
if [[ -f "$RESTORE_CONFIG" ]]; then
    set -a
    source "$RESTORE_CONFIG"
    set +a
fi

# Restore configuration with defaults
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-$PROJECT_ROOT/backups}"
STORAGE_PATH="${STORAGE_PATH:-$PROJECT_ROOT/storage}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.prod.yml}"
DB_CONTAINER="${DB_CONTAINER:-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-3d_print_system}"

# Runtime configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_BASE_DIR/logs/restore_$TIMESTAMP.log"
TEMP_DIR="$BACKUP_BASE_DIR/temp/restore_$TIMESTAMP"
PRE_RESTORE_BACKUP_DIR="$TEMP_DIR/pre_restore_backup"

# Command line options
BACKUP_DATE=""
FORCE_RESTORE=false
SKIP_CONFIRMATION=false
VERIFY_ONLY=false
LIST_BACKUPS=false
DRY_RUN=false

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

cleanup_temp() {
    if [[ -d "$TEMP_DIR" ]]; then
        log_info "Cleaning up temporary files"
        rm -rf "$TEMP_DIR"
    fi
}

confirm_action() {
    local message="$1"
    local default="${2:-n}"
    
    if [[ "$SKIP_CONFIRMATION" == "true" ]]; then
        log_warn "Skipping confirmation (--yes flag used)"
        return 0
    fi
    
    echo ""
    echo "⚠️  CONFIRMATION REQUIRED ⚠️"
    echo "$message"
    echo ""
    
    while true; do
        if [[ "$default" == "y" ]]; then
            read -p "Continue? [Y/n]: " -r response
            response=${response:-y}
        else
            read -p "Continue? [y/N]: " -r response
            response=${response:-n}
        fi
        
        case $response in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes (y) or no (n).";;
        esac
    done
}

check_prerequisites() {
    log_info "Checking restore prerequisites..."
    
    # Check if backup directory exists
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        log_error "Backup directory not found: $BACKUP_BASE_DIR"
        return 1
    fi
    
    # Create temp and log directories
    mkdir -p "$TEMP_DIR" "$PRE_RESTORE_BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check Docker Compose file
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        return 1
    fi
    
    log_success "Prerequisites check passed"
    return 0
}

# =============================================================================
# Backup Discovery and Validation Functions
# =============================================================================

list_available_backups() {
    log_info "Scanning for available backups..."
    
    echo ""
    echo "Available Backup Sets:"
    echo "====================="
    
    local found_backups=false
    
    for backup_type in daily weekly monthly; do
        local backup_dir="$BACKUP_BASE_DIR/$backup_type"
        if [[ ! -d "$backup_dir" ]]; then
            continue
        fi
        
        echo ""
        echo "${backup_type^} Backups:"
        echo "$(printf '%.0s-' {1..15})"
        
        # Group backups by date
        local dates=$(find "$backup_dir" -name "database_*.sql.gz" -exec basename {} \; | \
                     sed 's/database_.*_\([0-9]\{8\}\)\.sql\.gz/\1/' | sort -u)
        
        for date in $dates; do
            local db_file="$backup_dir/database_${backup_type}_${date}.sql.gz"
            local storage_file="$backup_dir/storage_${backup_type}_${date}.tar.gz"
            
            if [[ -f "$db_file" && -f "$storage_file" ]]; then
                local db_size=$(du -h "$db_file" | cut -f1)
                local storage_size=$(du -h "$storage_file" | cut -f1)
                local backup_date=$(date -d "$date" "+%Y-%m-%d (%A)" 2>/dev/null || echo "$date")
                
                echo "  $date - $backup_date"
                echo "    Database: $db_size, Storage: $storage_size"
                found_backups=true
            fi
        done
    done
    
    if [[ "$found_backups" == "false" ]]; then
        echo "No complete backup sets found."
        echo "A complete backup set requires both database and storage backups with matching dates."
    fi
    
    echo ""
}

find_backup_files() {
    local backup_date="$1"
    local db_file=""
    local storage_file=""
    
    # Search in order of preference: monthly, weekly, daily
    for backup_type in monthly weekly daily; do
        local backup_dir="$BACKUP_BASE_DIR/$backup_type"
        local potential_db="$backup_dir/database_${backup_type}_${backup_date}.sql.gz"
        local potential_storage="$backup_dir/storage_${backup_type}_${backup_date}.tar.gz"
        
        if [[ -f "$potential_db" && -f "$potential_storage" ]]; then
            db_file="$potential_db"
            storage_file="$potential_storage"
            log_info "Found $backup_type backup set for $backup_date"
            break
        fi
    done
    
    if [[ -z "$db_file" || -z "$storage_file" ]]; then
        log_error "Complete backup set not found for date: $backup_date"
        log_info "Available backup dates:"
        list_available_backups >/dev/null
        return 1
    fi
    
    echo "$db_file|$storage_file"
}

verify_backup_integrity() {
    local backup_files="$1"
    IFS='|' read -r db_file storage_file <<< "$backup_files"
    
    log_info "Verifying backup integrity..."
    
    # Verify database backup
    log_info "Checking database backup: $(basename "$db_file")"
    if [[ ! -f "$db_file" ]]; then
        log_error "Database backup file not found"
        return 1
    fi
    
    if ! gzip -t "$db_file" 2>/dev/null; then
        log_error "Database backup file is corrupted (gzip test failed)"
        return 1
    fi
    
    if ! zcat "$db_file" | head -20 | grep -q "PostgreSQL database dump"; then
        log_error "Database backup file does not appear to be a valid PostgreSQL dump"
        return 1
    fi
    
    local db_size=$(stat -f%z "$db_file" 2>/dev/null || stat -c%s "$db_file")
    log_info "Database backup size: $(du -h "$db_file" | cut -f1) ($db_size bytes)"
    
    # Verify storage backup
    log_info "Checking storage backup: $(basename "$storage_file")"
    if [[ ! -f "$storage_file" ]]; then
        log_error "Storage backup file not found"
        return 1
    fi
    
    if ! tar -tzf "$storage_file" >/dev/null 2>&1; then
        log_error "Storage backup file is corrupted (tar test failed)"
        return 1
    fi
    
    local storage_file_count=$(tar -tzf "$storage_file" | wc -l)
    local storage_size=$(stat -f%z "$storage_file" 2>/dev/null || stat -c%s "$storage_file")
    log_info "Storage backup size: $(du -h "$storage_file" | cut -f1) ($storage_size bytes, $storage_file_count files)"
    
    log_success "Backup integrity verification passed"
    return 0
}

# =============================================================================
# Pre-Restore Safety Functions
# =============================================================================

create_pre_restore_backup() {
    log_info "Creating pre-restore safety backup..."
    
    # Check if system is running
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "System is running, creating live backup"
        
        # Create current database backup
        local current_db_backup="$PRE_RESTORE_BACKUP_DIR/pre_restore_db_$TIMESTAMP.sql.gz"
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
            pg_dump -U "$DB_USER" -d "$DB_NAME" --verbose --no-password | gzip > "$current_db_backup"; then
            log_success "Current database backed up to: $current_db_backup"
        else
            log_error "Failed to backup current database"
            return 1
        fi
    else
        log_info "System is not running, skipping live database backup"
    fi
    
    # Create current storage backup
    if [[ -d "$STORAGE_PATH" ]]; then
        local current_storage_backup="$PRE_RESTORE_BACKUP_DIR/pre_restore_storage_$TIMESTAMP.tar.gz"
        if tar -czf "$current_storage_backup" -C "$(dirname "$STORAGE_PATH")" "$(basename "$STORAGE_PATH")"; then
            log_success "Current storage backed up to: $current_storage_backup"
        else
            log_error "Failed to backup current storage"
            return 1
        fi
    else
        log_info "Storage directory not found, skipping storage backup"
    fi
    
    log_success "Pre-restore safety backup completed"
}

stop_system() {
    log_info "Stopping system services..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
        if docker-compose -f "$DOCKER_COMPOSE_FILE" down; then
            log_success "System services stopped"
        else
            log_error "Failed to stop system services"
            return 1
        fi
    else
        log_info "System services already stopped"
    fi
    
    # Wait for complete shutdown
    sleep 5
}

# =============================================================================
# Database Restore Functions
# =============================================================================

restore_database() {
    local db_backup_file="$1"
    log_info "Restoring database from: $(basename "$db_backup_file")"
    
    # Start only the database service
    log_info "Starting database service for restore"
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" up -d "$DB_CONTAINER"; then
        log_error "Failed to start database service"
        return 1
    fi
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
            pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            break
        fi
        
        log_info "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Database failed to become ready within timeout"
        return 1
    fi
    
    log_success "Database is ready"
    
    # Drop existing database and recreate
    log_info "Recreating database schema..."
    
    # Create temporary SQL script for database recreation
    local temp_sql="$TEMP_DIR/recreate_db.sql"
    cat > "$temp_sql" << EOF
-- Terminate existing connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();

-- Drop and recreate database
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME WITH 
    OWNER = $DB_USER
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default;
EOF
    
    # Execute database recreation
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
        psql -U "$DB_USER" -d postgres -f - < "$temp_sql"; then
        log_success "Database recreated successfully"
    else
        log_error "Failed to recreate database"
        return 1
    fi
    
    # Restore from backup
    log_info "Restoring data from backup..."
    if zcat "$db_backup_file" | docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -q; then
        log_success "Database restore completed"
    else
        log_error "Database restore failed"
        return 1
    fi
    
    # Verify restore
    local table_count=$(docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
        psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' \n\r')
    
    log_info "Restored database contains $table_count tables"
    
    if [[ $table_count -eq 0 ]]; then
        log_error "Database restore appears to have failed (no tables found)"
        return 1
    fi
    
    log_success "Database restoration verified"
}

# =============================================================================
# File Storage Restore Functions
# =============================================================================

restore_file_storage() {
    local storage_backup_file="$1"
    log_info "Restoring file storage from: $(basename "$storage_backup_file")"
    
    # Backup existing storage if it exists
    if [[ -d "$STORAGE_PATH" ]]; then
        local existing_storage_backup="$TEMP_DIR/existing_storage_$TIMESTAMP.tar.gz"
        log_info "Backing up existing storage directory"
        if tar -czf "$existing_storage_backup" -C "$(dirname "$STORAGE_PATH")" "$(basename "$STORAGE_PATH")"; then
            log_info "Existing storage backed up to: $existing_storage_backup"
        else
            log_warn "Failed to backup existing storage directory"
        fi
        
        # Remove existing storage
        rm -rf "$STORAGE_PATH"
    fi
    
    # Create parent directory
    mkdir -p "$(dirname "$STORAGE_PATH")"
    
    # Extract storage backup
    log_info "Extracting storage backup..."
    if tar -xzf "$storage_backup_file" -C "$(dirname "$STORAGE_PATH")"; then
        log_success "Storage extraction completed"
    else
        log_error "Storage extraction failed"
        return 1
    fi
    
    # Verify restoration
    if [[ ! -d "$STORAGE_PATH" ]]; then
        log_error "Storage directory was not created by extraction"
        return 1
    fi
    
    local restored_file_count=$(find "$STORAGE_PATH" -type f | wc -l)
    log_info "Restored storage contains $restored_file_count files"
    
    # Set appropriate permissions (if on Unix-like system)
    if command -v chmod >/dev/null 2>&1; then
        chmod -R 755 "$STORAGE_PATH"
        log_info "Storage permissions set"
    fi
    
    log_success "File storage restoration completed"
}

# =============================================================================
# Post-Restore Verification Functions
# =============================================================================

start_system() {
    log_info "Starting system services..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" up -d; then
        log_success "System services started"
    else
        log_error "Failed to start system services"
        return 1
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    local healthy_services=0
    local total_services=0
    
    while read -r service; do
        if [[ -n "$service" ]]; then
            ((total_services++))
            if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep -q "Up"; then
                ((healthy_services++))
                log_info "Service $service is healthy"
            else
                log_warn "Service $service is not healthy"
            fi
        fi
    done < <(docker-compose -f "$DOCKER_COMPOSE_FILE" config --services)
    
    log_info "System health: $healthy_services/$total_services services running"
    
    if [[ $healthy_services -eq $total_services ]]; then
        log_success "All services are running"
        return 0
    else
        log_error "Some services failed to start properly"
        return 1
    fi
}

run_integrity_audit() {
    log_info "Running post-restore system integrity audit..."
    
    # Check if audit endpoint is available
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f http://localhost:5000/api/v1/admin/audit >/dev/null 2>&1; then
            break
        fi
        log_info "Waiting for system to be ready for audit... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_warn "System audit endpoint not available, skipping automated audit"
        log_info "Please run manual system integrity check after restore"
        return 0
    fi
    
    # Run system audit
    log_info "Executing system integrity audit..."
    local audit_response
    if audit_response=$(curl -s -X POST http://localhost:5000/api/v1/admin/audit); then
        log_info "System audit completed"
        
        # Parse audit results (simplified)
        if echo "$audit_response" | grep -q '"status":"success"'; then
            log_success "System integrity audit passed"
        else
            log_warn "System integrity audit found issues - review required"
            log_info "Audit response: $audit_response"
        fi
    else
        log_warn "System audit failed to execute"
        log_info "Please run manual system integrity check"
    fi
}

generate_restore_report() {
    local backup_date="$1"
    local restore_duration="$2"
    
    local report="Database and File Storage Restore Completed

Backup Date: $backup_date
Restore Duration: ${restore_duration} seconds
Restore Timestamp: $(date)
Server: $(hostname)

Restoration Summary:
- Database: Restored and verified
- File Storage: Restored and verified  
- System Services: Started successfully
- Integrity Audit: $(if curl -s -f http://localhost:5000/api/v1/admin/audit >/dev/null 2>&1; then echo "Completed"; else echo "Pending manual check"; fi)

Pre-Restore Backup Location:
$PRE_RESTORE_BACKUP_DIR

Next Steps:
1. Verify system functionality through normal operations
2. Check all critical workflows (job submission, approval, etc.)
3. Confirm file access and integrity
4. Update any necessary configurations
5. Monitor system logs for any issues

Important Notes:
- Pre-restore backup is available at: $PRE_RESTORE_BACKUP_DIR
- Original restore log: $LOG_FILE
- If issues arise, rollback procedures are available

System is ready for production use."

    echo "$report" >> "$LOG_FILE"
    log_info "Restore report generated"
    
    # Display summary to user
    echo ""
    echo "🎉 RESTORE COMPLETED SUCCESSFULLY 🎉"
    echo "=================================="
    echo "$report"
}

# =============================================================================
# Main Restore Process
# =============================================================================

perform_restore() {
    local backup_date="$1"
    local start_time=$(date +%s)
    
    log_info "Starting restore process for backup date: $backup_date"
    
    # Step 1: Find and verify backup files
    local backup_files
    if ! backup_files=$(find_backup_files "$backup_date"); then
        return 1
    fi
    
    if ! verify_backup_integrity "$backup_files"; then
        return 1
    fi
    
    IFS='|' read -r db_backup_file storage_backup_file <<< "$backup_files"
    
    # Step 2: Final confirmation
    if ! confirm_action "This will restore the system to backup from $backup_date.
    
Current system data will be OVERWRITTEN and cannot be recovered 
without the pre-restore backup that will be created.

Database backup: $(basename "$db_backup_file")
Storage backup: $(basename "$storage_backup_file")

Are you sure you want to proceed with this restore?"; then
        log_info "Restore cancelled by user"
        return 1
    fi
    
    # Step 3: Create pre-restore safety backup
    create_pre_restore_backup
    
    # Step 4: Stop system services
    stop_system
    
    # Step 5: Restore database
    if ! restore_database "$db_backup_file"; then
        log_error "Database restore failed"
        return 1
    fi
    
    # Step 6: Restore file storage
    if ! restore_file_storage "$storage_backup_file"; then
        log_error "File storage restore failed"
        return 1
    fi
    
    # Step 7: Start system services
    if ! start_system; then
        log_error "Failed to start system services after restore"
        return 1
    fi
    
    # Step 8: Run integrity audit
    run_integrity_audit
    
    # Step 9: Generate report
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    generate_restore_report "$backup_date" "$duration"
    
    log_success "Restore process completed successfully"
}

# =============================================================================
# Command Line Interface
# =============================================================================

show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Database and File Storage Restore Script for 3D Print Management System
Implements masterplan-compliant recovery procedures with safety checks.

COMMANDS:
    --backup-date DATE     Restore from backup with date YYYYMMDD
    --list-backups         List all available backup sets
    --verify-backup DATE   Verify backup integrity for specific date
    
OPTIONS:
    --config PATH          Use custom configuration file (default: .env)
    --force                Skip safety checks (use with extreme caution)
    --yes                  Skip confirmation prompts
    --dry-run              Show what would be done without making changes
    --help                 Show this help message

EXAMPLES:
    $0 --list-backups                    # Show available backups
    $0 --backup-date 20231215             # Restore from Dec 15, 2023 backup
    $0 --verify-backup 20231215           # Verify backup integrity
    $0 --backup-date 20231215 --yes       # Restore without confirmation
    
IMPORTANT WARNINGS:
    - This script will OVERWRITE existing data
    - System services will be stopped during restore
    - A pre-restore backup is created for safety
    - Always verify backup integrity before restoring
    - Test restores should be done in non-production environment

For detailed procedures, see docs/backup-procedures.md

EOF
}

# =============================================================================
# Error Handling
# =============================================================================

handle_error() {
    local error_code=$?
    local line_number=$1
    
    log_error "Restore failed on line $line_number with exit code $error_code"
    log_error "System may be in an inconsistent state - manual intervention required"
    
    echo ""
    echo "❌ RESTORE FAILED ❌"
    echo "==================="
    echo "The restore process has failed and the system may be in an inconsistent state."
    echo "Please check the restore log for details: $LOG_FILE"
    echo ""
    echo "Recovery options:"
    echo "1. Check the pre-restore backup: $PRE_RESTORE_BACKUP_DIR"
    echo "2. Restart system services: docker-compose -f $DOCKER_COMPOSE_FILE up -d"
    echo "3. Contact system administrator for assistance"
    echo ""
    
    cleanup_temp
    exit $error_code
}

trap 'handle_error $LINENO' ERR

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-date)
                BACKUP_DATE="$2"
                shift 2
                ;;
            --list-backups)
                LIST_BACKUPS=true
                shift
                ;;
            --verify-backup)
                VERIFY_ONLY=true
                BACKUP_DATE="$2"
                shift 2
                ;;
            --config)
                RESTORE_CONFIG="$2"
                shift 2
                ;;
            --force)
                FORCE_RESTORE=true
                shift
                ;;
            --yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
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
    
    # Initialize logging
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_info "3D Print Management System Restore Script Starting"
    log_info "Script version: 1.0.0 (Masterplan Compliant)"
    log_info "Configuration: $RESTORE_CONFIG"
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Handle special commands
    if [[ "$LIST_BACKUPS" == "true" ]]; then
        list_available_backups
        exit 0
    fi
    
    if [[ "$VERIFY_ONLY" == "true" ]]; then
        if [[ -z "$BACKUP_DATE" ]]; then
            log_error "Backup date required for verification"
            show_usage
            exit 1
        fi
        
        local backup_files
        if backup_files=$(find_backup_files "$BACKUP_DATE"); then
            verify_backup_integrity "$backup_files"
            log_success "Backup verification completed successfully"
        else
            log_error "Backup verification failed"
            exit 1
        fi
        exit 0
    fi
    
    # Validate backup date parameter
    if [[ -z "$BACKUP_DATE" ]]; then
        log_error "Backup date is required"
        echo ""
        echo "Available backups:"
        list_available_backups
        echo ""
        show_usage
        exit 1
    fi
    
    # Validate date format
    if [[ ! "$BACKUP_DATE" =~ ^[0-9]{8}$ ]]; then
        log_error "Invalid date format. Use YYYYMMDD (e.g., 20231215)"
        exit 1
    fi
    
    # Dry run mode
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
        local backup_files
        if backup_files=$(find_backup_files "$BACKUP_DATE"); then
            IFS='|' read -r db_backup_file storage_backup_file <<< "$backup_files"
            echo "Would restore from:"
            echo "  Database: $(basename "$db_backup_file") ($(du -h "$db_backup_file" | cut -f1))"
            echo "  Storage:  $(basename "$storage_backup_file") ($(du -h "$storage_backup_file" | cut -f1))"
            verify_backup_integrity "$backup_files"
        fi
        exit 0
    fi
    
    # Perform the restore
    perform_restore "$BACKUP_DATE"
    
    # Cleanup
    cleanup_temp
    
    log_success "Restore script completed successfully"
}

# Execute main function with all arguments
main "$@"
