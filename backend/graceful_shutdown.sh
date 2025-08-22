#!/bin/bash

# Graceful shutdown script for 3D Print Management System backend
# This script handles proper cleanup and shutdown procedures

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Function to handle cleanup
cleanup() {
    log "Starting graceful shutdown..."
    
    # Stop accepting new requests (if using a reverse proxy, this would be handled there)
    log "Stopping new request acceptance..."
    
    # Wait for current requests to complete (give them time to finish)
    log "Waiting for current requests to complete..."
    sleep 5
    
    # Close database connections gracefully
    log "Closing database connections..."
    # This would be handled by the Flask app's shutdown hooks
    
    # Stop background workers gracefully
    log "Stopping background workers..."
    # Send SIGTERM to RQ workers if they're running
    if pgrep -f "rq worker" > /dev/null; then
        pkill -TERM -f "rq worker"
        sleep 3
        # Force kill if still running
        if pgrep -f "rq worker" > /dev/null; then
            warn "Workers still running, force killing..."
            pkill -KILL -f "rq worker"
        fi
    fi
    
    # Close Redis connections
    log "Closing Redis connections..."
    # This would be handled by the Flask app's shutdown hooks
    
    # Clean up temporary files
    log "Cleaning up temporary files..."
    find /tmp -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
    
    log "Graceful shutdown completed"
}

# Function to handle signals
handle_signal() {
    local signal=$1
    log "Received signal $signal, initiating graceful shutdown..."
    cleanup
    exit 0
}

# Set up signal handlers
trap 'handle_signal SIGTERM' SIGTERM
trap 'handle_signal SIGINT' SIGINT

# Main function
main() {
    log "Graceful shutdown script initialized"
    log "Waiting for shutdown signals..."
    
    # Keep the script running to handle signals
    while true; do
        sleep 1
    done
}

# Run main function
main "$@"
