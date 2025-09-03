#!/bin/bash

# =============================================================================
# Comprehensive Database and File Storage Backup Script
# 3D Print Management System - Masterplan Compliant Backup Strategy
# =============================================================================
#
# This script implements the backup strategy defined in Section 5.8 of the
# masterplan, providing synchronized database and file storage backups with
# sophisticated retention, monitoring, and off-site storage capabilities.
#
# Features:
# - Synchronized PostgreSQL database and file storage backup
# - Multi-tier retention policy (14 days/2 months/1 year)
# - Off-site storage support
# - Backup verification and integrity checks
# - Email notifications for success/failure
# - Comprehensive logging
#
# Usage:
#   ./backup_database.sh [--config /path/to/config] [--test-mode] [--verify-only]
#
# Configuration:
#   Set environment variables or create a config file (see BACKUP_CONFIG below)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# =============================================================================
# Configuration and Environment Setup
# =============================================================================

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_CONFIG="$PROJECT_ROOT/.env"

# Load configuration from file or environment
BACKUP_CONFIG="${BACKUP_CONFIG:-$DEFAULT_CONFIG}"
if [[ -f "$BACKUP_CONFIG" ]]; then
    # Load config but preserve existing env vars
    set -a
    source "$BACKUP_CONFIG"
    set +a
fi

# Backup configuration with defaults
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-$PROJECT_ROOT/backups}"
STORAGE_PATH="${STORAGE_PATH:-$PROJECT_ROOT/storage}"
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.prod.yml}"
DB_CONTAINER="${DB_CONTAINER:-db}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-3d_print_system}"

# Off-site storage configuration
OFFSITE_ENABLED="${OFFSITE_ENABLED:-false}"
OFFSITE_TYPE="${OFFSITE_TYPE:-rsync}"  # rsync, s3, scp
OFFSITE_DESTINATION="${OFFSITE_DESTINATION:-}"  # destination path/url
OFFSITE_OPTIONS="${OFFSITE_OPTIONS:-}"

# Email notification configuration
EMAIL_ENABLED="${EMAIL_ENABLED:-false}"
EMAIL_TO="${EMAIL_TO:-}"
EMAIL_FROM="${EMAIL_FROM:-backup@localhost}"
EMAIL_SMTP_HOST="${EMAIL_SMTP_HOST:-localhost}"
EMAIL_SUBJECT_PREFIX="${EMAIL_SUBJECT_PREFIX:-[3D Print Backup]}"

# Retention policy (masterplan Section 5.8)
DAILY_RETENTION_DAYS=14
WEEKLY_RETENTION_MONTHS=2
MONTHLY_RETENTION_YEARS=1

# Runtime configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_SHORT=$(date +%Y%m%d)
LOG_FILE="$BACKUP_BASE_DIR/logs/backup_$TIMESTAMP.log"
TEMP_DIR="$BACKUP_BASE_DIR/temp"
TEST_MODE="${TEST_MODE:-false}"

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

send_email() {
    local subject="$1"
    local message="$2"
    local is_error="${3:-false}"
    
    if [[ "$EMAIL_ENABLED" != "true" ]] || [[ -z "$EMAIL_TO" ]]; then
        return 0
    fi
    
    local full_subject="$EMAIL_SUBJECT_PREFIX $subject"
    local body="3D Print Management System Backup Report

$message

Timestamp: $(date)
Server: $(hostname)
Backup Location: $BACKUP_BASE_DIR

---
This is an automated message from the 3D Print Management System backup service."

    if command -v mail >/dev/null 2>&1; then
        echo "$body" | mail -s "$full_subject" "$EMAIL_TO"
        log_info "Email notification sent to $EMAIL_TO"
    else
        log_warn "Email notification requested but 'mail' command not available"
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running in correct environment
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        return 1
    fi
    
    # Check if Docker Compose is available and database is running
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "$DB_CONTAINER"; then
        log_error "Database container ($DB_CONTAINER) not found or not running"
        return 1
    fi
    
    # Check storage directory
    if [[ ! -d "$STORAGE_PATH" ]]; then
        log_error "Storage directory not found: $STORAGE_PATH"
        return 1
    fi
    
    # Create backup directories
    mkdir -p "$BACKUP_BASE_DIR"/{daily,weekly,monthly,logs}
    mkdir -p "$TEMP_DIR"
    
    log_success "Prerequisites check passed"
    return 0
}

# =============================================================================
# Database Backup Functions
# =============================================================================

backup_database() {
    log_info "Starting database backup..."
    
    local backup_file="$TEMP_DIR/db_backup_$TIMESTAMP.sql"
    local compressed_file="$backup_file.gz"
    
    # Create database dump with verbose output
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T "$DB_CONTAINER" \
        pg_dump -U "$DB_USER" -d "$DB_NAME" \
        --verbose --no-password --format=plain --no-owner --no-privileges \
        > "$backup_file" 2>>"$LOG_FILE"; then
        
        log_success "Database dump completed: $(du -h "$backup_file" | cut -f1)"
    else
        log_error "Database dump failed"
        return 1
    fi
    
    # Compress the backup
    if gzip "$backup_file"; then
        log_success "Database backup compressed: $(du -h "$compressed_file" | cut -f1)"
        echo "$compressed_file"  # Return compressed file path
    else
        log_error "Database backup compression failed"
        return 1
    fi
}

verify_database_backup() {
    local backup_file="$1"
    log_info "Verifying database backup integrity..."
    
    # Basic integrity checks
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Check if file is a valid gzip file
    if ! gzip -t "$backup_file" 2>/dev/null; then
        log_error "Backup file is not a valid gzip file"
        return 1
    fi
    
    # Check if decompressed content looks like a SQL dump
    if ! zcat "$backup_file" | head -20 | grep -q "PostgreSQL database dump"; then
        log_error "Backup file does not appear to be a valid PostgreSQL dump"
        return 1
    fi
    
    # Check minimum file size (should be at least a few KB for even empty DB)
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    if [[ $file_size -lt 1024 ]]; then
        log_error "Backup file suspiciously small: $file_size bytes"
        return 1
    fi
    
    log_success "Database backup verification passed"
    return 0
}

# =============================================================================
# File Storage Backup Functions
# =============================================================================

backup_file_storage() {
    log_info "Starting file storage backup..."
    
    local backup_file="$TEMP_DIR/storage_backup_$TIMESTAMP.tar.gz"
    
    # Create compressed archive of storage directory
    if tar -czf "$backup_file" -C "$(dirname "$STORAGE_PATH")" \
        --exclude='*.tmp' --exclude='*.lock' \
        "$(basename "$STORAGE_PATH")" 2>>"$LOG_FILE"; then
        
        log_success "File storage backup completed: $(du -h "$backup_file" | cut -f1)"
        echo "$backup_file"  # Return backup file path
    else
        log_error "File storage backup failed"
        return 1
    fi
}

verify_file_storage_backup() {
    local backup_file="$1"
    log_info "Verifying file storage backup integrity..."
    
    # Check if file exists and is valid tar.gz
    if [[ ! -f "$backup_file" ]]; then
        log_error "Storage backup file not found: $backup_file"
        return 1
    fi
    
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_error "Storage backup file is not a valid tar.gz archive"
        return 1
    fi
    
    # Count files in backup and compare with source
    local backup_file_count=$(tar -tzf "$backup_file" | wc -l)
    local source_file_count=$(find "$STORAGE_PATH" -type f | wc -l)
    
    log_info "File count - Source: $source_file_count, Backup: $backup_file_count"
    
    # Allow for small discrepancies due to temporary files
    local diff=$((source_file_count - backup_file_count))
    if [[ $diff -lt 0 ]]; then diff=$((-diff)); fi
    if [[ $diff -gt 5 ]]; then
        log_error "Significant file count mismatch between source and backup"
        return 1
    fi
    
    log_success "File storage backup verification passed"
    return 0
}

# =============================================================================
# Backup Organization and Retention Functions
# =============================================================================

organize_backups() {
    local db_backup="$1"
    local storage_backup="$2"
    
    log_info "Organizing backups with retention policy..."
    
    # Determine backup type and destination
    local day_of_week=$(date +%u)  # 1=Monday, 7=Sunday
    local day_of_month=$(date +%d)
    local backup_type="daily"
    local dest_dir="$BACKUP_BASE_DIR/daily"
    
    # Weekly backup (Sunday)
    if [[ $day_of_week -eq 7 ]]; then
        backup_type="weekly"
        dest_dir="$BACKUP_BASE_DIR/weekly"
    fi
    
    # Monthly backup (1st of month)
    if [[ $day_of_month -eq 01 ]]; then
        backup_type="monthly"
        dest_dir="$BACKUP_BASE_DIR/monthly"
    fi
    
    log_info "Creating $backup_type backup in $dest_dir"
    
    # Copy backups to appropriate directory with naming convention
    local db_dest="$dest_dir/database_${backup_type}_$DATE_SHORT.sql.gz"
    local storage_dest="$dest_dir/storage_${backup_type}_$DATE_SHORT.tar.gz"
    
    cp "$db_backup" "$db_dest"
    cp "$storage_backup" "$storage_dest"
    
    log_success "Backups organized as $backup_type backups"
    
    # Apply retention policy
    apply_retention_policy
}

apply_retention_policy() {
    log_info "Applying retention policy..."
    
    # Daily backups: keep 14 days
    find "$BACKUP_BASE_DIR/daily" -name "*.gz" -mtime +$DAILY_RETENTION_DAYS -delete 2>/dev/null || true
    
    # Weekly backups: keep 2 months (8-9 weeks)
    local weekly_retention_days=$((WEEKLY_RETENTION_MONTHS * 30))
    find "$BACKUP_BASE_DIR/weekly" -name "*.gz" -mtime +$weekly_retention_days -delete 2>/dev/null || true
    
    # Monthly backups: keep 1 year
    local monthly_retention_days=$((MONTHLY_RETENTION_YEARS * 365))
    find "$BACKUP_BASE_DIR/monthly" -name "*.gz" -mtime +$monthly_retention_days -delete 2>/dev/null || true
    
    # Clean old log files (keep 30 days)
    find "$BACKUP_BASE_DIR/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_success "Retention policy applied"
}

# =============================================================================
# Off-Site Storage Functions
# =============================================================================

sync_to_offsite() {
    if [[ "$OFFSITE_ENABLED" != "true" ]] || [[ -z "$OFFSITE_DESTINATION" ]]; then
        log_info "Off-site storage not configured, skipping"
        return 0
    fi
    
    log_info "Syncing backups to off-site storage..."
    
    case "$OFFSITE_TYPE" in
        "rsync")
            if command -v rsync >/dev/null 2>&1; then
                # shellcheck disable=SC2086
                if rsync -avz --delete $OFFSITE_OPTIONS "$BACKUP_BASE_DIR/" "$OFFSITE_DESTINATION/"; then
                    log_success "Off-site sync completed via rsync"
                else
                    log_error "Off-site sync failed via rsync"
                    return 1
                fi
            else
                log_error "rsync command not available"
                return 1
            fi
            ;;
        "s3")
            if command -v aws >/dev/null 2>&1; then
                # shellcheck disable=SC2086
                if aws s3 sync $OFFSITE_OPTIONS "$BACKUP_BASE_DIR/" "$OFFSITE_DESTINATION/"; then
                    log_success "Off-site sync completed via AWS S3"
                else
                    log_error "Off-site sync failed via AWS S3"
                    return 1
                fi
            else
                log_error "aws command not available"
                return 1
            fi
            ;;
        "scp")
            if command -v scp >/dev/null 2>&1; then
                # shellcheck disable=SC2086
                if scp -r $OFFSITE_OPTIONS "$BACKUP_BASE_DIR/" "$OFFSITE_DESTINATION/"; then
                    log_success "Off-site sync completed via SCP"
                else
                    log_error "Off-site sync failed via SCP"
                    return 1
                fi
            else
                log_error "scp command not available"
                return 1
            fi
            ;;
        *)
            log_error "Unknown off-site storage type: $OFFSITE_TYPE"
            return 1
            ;;
    esac
}

# =============================================================================
# Main Backup Process
# =============================================================================

perform_backup() {
    local start_time=$(date +%s)
    log_info "Starting comprehensive backup process..."
    
    # Step 1: Database backup (must be first for synchronization)
    local db_backup
    if ! db_backup=$(backup_database); then
        log_error "Database backup failed, aborting"
        return 1
    fi
    
    # Step 2: Verify database backup
    if ! verify_database_backup "$db_backup"; then
        log_error "Database backup verification failed, aborting"
        return 1
    fi
    
    # Step 3: File storage backup (immediately after database for sync)
    local storage_backup
    if ! storage_backup=$(backup_file_storage); then
        log_error "File storage backup failed, aborting"
        return 1
    fi
    
    # Step 4: Verify file storage backup
    if ! verify_file_storage_backup "$storage_backup"; then
        log_error "File storage backup verification failed, aborting"
        return 1
    fi
    
    # Step 5: Organize backups with retention policy
    organize_backups "$db_backup" "$storage_backup"
    
    # Step 6: Sync to off-site storage
    if ! sync_to_offsite; then
        log_warn "Off-site sync failed, but local backups completed successfully"
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_success "Backup process completed successfully in ${duration}s"
    
    # Generate backup report
    generate_backup_report "$duration"
}

generate_backup_report() {
    local duration="$1"
    local report="Backup completed successfully!

Duration: ${duration} seconds
Backup Location: $BACKUP_BASE_DIR
Backup Type: $(date +%u | sed 's/7/weekly/;s/1/daily/;t;s/.*/daily/')

Database Backup: Completed and verified
File Storage Backup: Completed and verified
Off-site Sync: $(if [[ "$OFFSITE_ENABLED" == "true" ]]; then echo "Completed"; else echo "Not configured"; fi)

Retention Policy Applied:
- Daily backups: $DAILY_RETENTION_DAYS days
- Weekly backups: $WEEKLY_RETENTION_MONTHS months  
- Monthly backups: $MONTHLY_RETENTION_YEARS years

Storage Usage:
$(du -sh "$BACKUP_BASE_DIR"/* 2>/dev/null | head -10)

Next Steps:
- Backups are ready for use
- Quarterly restore test recommended (see backup-procedures.md)
- Monitor backup logs in $BACKUP_BASE_DIR/logs/"

    echo "$report" >> "$LOG_FILE"
    send_email "Backup Successful" "$report"
    
    log_info "Backup report generated and notifications sent"
}

# =============================================================================
# Error Handling and Recovery
# =============================================================================

handle_error() {
    local error_code=$?
    local line_number=$1
    
    log_error "Backup failed on line $line_number with exit code $error_code"
    
    local error_report="BACKUP FAILED

Error Code: $error_code
Line Number: $line_number
Timestamp: $(date)
Server: $(hostname)

Please check the backup logs for details:
$LOG_FILE

This requires immediate attention to ensure data protection."

    send_email "BACKUP FAILED" "$error_report" true
    cleanup_temp
    exit $error_code
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# =============================================================================
# Command Line Interface
# =============================================================================

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Comprehensive backup script for 3D Print Management System
Implements masterplan-compliant backup strategy with database and file storage.

OPTIONS:
    --config PATH       Use custom configuration file (default: .env)
    --test-mode         Run in test mode (validate setup but don't create backups)
    --verify-only       Only verify existing backups, don't create new ones
    --help              Show this help message

CONFIGURATION:
    Set environment variables or create configuration file with:
    
    BACKUP_BASE_DIR     Base directory for backups (default: ./backups)
    STORAGE_PATH        Path to storage directory to backup
    DOCKER_COMPOSE_FILE Docker compose file path
    DB_CONTAINER        Database container name
    DB_USER             Database user
    DB_NAME             Database name
    
    OFFSITE_ENABLED     Enable off-site storage (true/false)
    OFFSITE_TYPE        Off-site type (rsync/s3/scp)
    OFFSITE_DESTINATION Off-site destination path/URL
    
    EMAIL_ENABLED       Enable email notifications (true/false)
    EMAIL_TO            Notification email address

EXAMPLES:
    $0                                  # Run full backup
    $0 --test-mode                      # Test configuration
    $0 --config /etc/backup.conf       # Use custom config
    
For more information, see docs/backup-procedures.md

EOF
}

verify_existing_backups() {
    log_info "Verifying existing backups..."
    
    local verified=0
    local failed=0
    
    for backup_dir in "$BACKUP_BASE_DIR"/{daily,weekly,monthly}; do
        if [[ ! -d "$backup_dir" ]]; then
            continue
        fi
        
        for db_backup in "$backup_dir"/database_*.sql.gz; do
            if [[ -f "$db_backup" ]]; then
                if verify_database_backup "$db_backup"; then
                    ((verified++))
                else
                    ((failed++))
                    log_error "Failed verification: $db_backup"
                fi
            fi
        done
        
        for storage_backup in "$backup_dir"/storage_*.tar.gz; do
            if [[ -f "$storage_backup" ]]; then
                if verify_file_storage_backup "$storage_backup"; then
                    ((verified++))
                else
                    ((failed++))
                    log_error "Failed verification: $storage_backup"
                fi
            fi
        done
    done
    
    log_info "Backup verification complete: $verified passed, $failed failed"
    return $failed
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                BACKUP_CONFIG="$2"
                shift 2
                ;;
            --test-mode)
                TEST_MODE=true
                shift
                ;;
            --verify-only)
                VERIFY_ONLY=true
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
    
    log_info "3D Print Management System Backup Script Starting"
    log_info "Script version: 1.0.0 (Masterplan Compliant)"
    log_info "Configuration: $BACKUP_CONFIG"
    log_info "Test mode: $TEST_MODE"
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Handle special modes
    if [[ "${VERIFY_ONLY:-false}" == "true" ]]; then
        verify_existing_backups
        exit $?
    fi
    
    if [[ "$TEST_MODE" == "true" ]]; then
        log_info "Test mode: Configuration validated successfully"
        log_info "Backup would be created in: $BACKUP_BASE_DIR"
        log_info "Storage path: $STORAGE_PATH"
        log_info "Off-site storage: $(if [[ "$OFFSITE_ENABLED" == "true" ]]; then echo "Enabled ($OFFSITE_TYPE)"; else echo "Disabled"; fi)"
        log_info "Email notifications: $(if [[ "$EMAIL_ENABLED" == "true" ]]; then echo "Enabled ($EMAIL_TO)"; else echo "Disabled"; fi)"
        exit 0
    fi
    
    # Perform the backup
    perform_backup
    
    # Cleanup
    cleanup_temp
    
    log_success "Backup script completed successfully"
}

# Execute main function with all arguments
main "$@"
