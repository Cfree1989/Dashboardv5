#!/bin/bash

# Comprehensive health check script for 3D Print Management System backend
# This script checks multiple aspects of the application health

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
HEALTH_ENDPOINT="http://localhost:5000/api/v1/health"
DB_CHECK_ENDPOINT="http://localhost:5000/api/v1/health/db"
REDIS_CHECK_ENDPOINT="http://localhost:5000/api/v1/health/redis"
STORAGE_CHECK_ENDPOINT="http://localhost:5000/api/v1/health/storage"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to check if a service is responding
check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-10}
    
    log "Checking $name at $url"
    
    if curl -f -s --max-time $timeout "$url" > /dev/null 2>&1; then
        log "$name is healthy"
        return 0
    else
        error "$name is not responding"
        return 1
    fi
}

# Function to check application health
check_app_health() {
    log "Checking application health..."
    
    if ! check_service "Application" "$HEALTH_ENDPOINT" 15; then
        return 1
    fi
    
    # Check if the response contains expected content
    response=$(curl -s --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "")
    if [[ "$response" == *"status"* ]] && [[ "$response" == *"healthy"* ]]; then
        log "Application health endpoint returned healthy status"
    else
        warn "Application health endpoint response format unexpected"
    fi
    
    return 0
}

# Function to check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    if check_service "Database" "$DB_CHECK_ENDPOINT" 15; then
        log "Database is accessible"
        return 0
    else
        error "Database connectivity check failed"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    log "Checking Redis connectivity..."
    
    if check_service "Redis" "$REDIS_CHECK_ENDPOINT" 10; then
        log "Redis is accessible"
        return 0
    else
        error "Redis connectivity check failed"
        return 1
    fi
}

# Function to check storage accessibility
check_storage() {
    log "Checking storage accessibility..."
    
    if check_service "Storage" "$STORAGE_CHECK_ENDPOINT" 10; then
        log "Storage is accessible"
        return 0
    else
        warn "Storage accessibility check failed (non-critical)"
        return 0  # Storage issues are not critical for basic health
    fi
}

# Function to check system resources
check_resources() {
    log "Checking system resources..."
    
    # Check available disk space
    disk_usage=$(df /app/storage | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        log "Disk usage is acceptable: ${disk_usage}%"
    else
        warn "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check available memory
    mem_available=$(free -m | awk 'NR==2{printf "%.1f", $7*100/$2}')
    if (( $(echo "$mem_available > 10" | bc -l) )); then
        log "Memory usage is acceptable: ${mem_available}% available"
    else
        warn "Memory usage is high: ${mem_available}% available"
    fi
    
    return 0
}

# Main health check function
main() {
    log "Starting comprehensive health check..."
    
    local exit_code=0
    
    # Check application health (primary check)
    if ! check_app_health; then
        exit_code=1
    fi
    
    # Check database connectivity
    if ! check_database; then
        exit_code=1
    fi
    
    # Check Redis connectivity
    if ! check_redis; then
        exit_code=1
    fi
    
    # Check storage accessibility (non-critical)
    check_storage
    
    # Check system resources (non-critical)
    check_resources
    
    if [ $exit_code -eq 0 ]; then
        log "All critical health checks passed"
    else
        error "Some critical health checks failed"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"
