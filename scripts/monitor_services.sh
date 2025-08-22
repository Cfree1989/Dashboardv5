#!/bin/bash

# Comprehensive monitoring script for 3D Print Management System
# This script provides detailed monitoring and debugging information

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
SERVICES=("backend" "frontend" "db" "redis" "worker")

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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if Docker Compose is running
check_compose_status() {
    log "Checking Docker Compose status..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        error "Docker Compose services are not running"
        return 1
    fi
    
    log "Docker Compose services are running"
    return 0
}

# Function to get service status
get_service_status() {
    local service=$1
    docker-compose -f "$COMPOSE_FILE" ps "$service" --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Function to check service health
check_service_health() {
    local service=$1
    
    info "Checking health for service: $service"
    
    case $service in
        "backend")
            if curl -f -s --max-time 10 "http://localhost:5000/api/v1/health" > /dev/null 2>&1; then
                log "Backend health check passed"
                return 0
            else
                error "Backend health check failed"
                return 1
            fi
            ;;
        "frontend")
            if curl -f -s --max-time 10 "http://localhost:3000/" > /dev/null 2>&1; then
                log "Frontend health check passed"
                return 0
            else
                error "Frontend health check failed"
                return 1
            fi
            ;;
        "db")
            if docker-compose -f "$COMPOSE_FILE" exec -T db pg_isready -U postgres > /dev/null 2>&1; then
                log "Database health check passed"
                return 0
            else
                error "Database health check failed"
                return 1
            fi
            ;;
        "redis")
            if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
                log "Redis health check passed"
                return 0
            else
                error "Redis health check failed"
                return 1
            fi
            ;;
        "worker")
            # Check if worker is running and can connect to Redis
            if docker-compose -f "$COMPOSE_FILE" exec -T worker rq info > /dev/null 2>&1; then
                log "Worker health check passed"
                return 0
            else
                error "Worker health check failed"
                return 1
            fi
            ;;
        *)
            warn "Unknown service: $service"
            return 1
            ;;
    esac
}

# Function to get service logs
get_service_logs() {
    local service=$1
    local lines=${2:-50}
    
    info "Getting logs for service: $service (last $lines lines)"
    echo -e "${CYAN}=== $service logs ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail="$lines" "$service"
    echo ""
}

# Function to check resource usage
check_resource_usage() {
    log "Checking resource usage..."
    
    echo -e "${CYAN}=== Container Resource Usage ===${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    echo ""
    
    echo -e "${CYAN}=== System Resource Usage ===${NC}"
    echo "Memory Usage:"
    free -h
    echo ""
    echo "Disk Usage:"
    df -h
    echo ""
}

# Function to check network connectivity
check_network_connectivity() {
    log "Checking network connectivity..."
    
    echo -e "${CYAN}=== Network Connectivity ===${NC}"
    
    # Check if services can reach each other
    local services=("backend" "frontend" "db" "redis" "worker")
    
    for service in "${services[@]}"; do
        info "Checking network for $service"
        docker-compose -f "$COMPOSE_FILE" exec -T "$service" ping -c 1 db > /dev/null 2>&1 && \
            log "$service can reach database" || \
            error "$service cannot reach database"
        
        docker-compose -f "$COMPOSE_FILE" exec -T "$service" ping -c 1 redis > /dev/null 2>&1 && \
            log "$service can reach Redis" || \
            error "$service cannot reach Redis"
    done
    echo ""
}

# Function to check API endpoints
check_api_endpoints() {
    log "Checking API endpoints..."
    
    echo -e "${CYAN}=== API Endpoint Health ===${NC}"
    
    local endpoints=(
        "http://localhost:5000/api/v1/health"
        "http://localhost:5000/api/v1/health/db"
        "http://localhost:5000/api/v1/health/redis"
        "http://localhost:5000/api/v1/health/storage"
        "http://localhost:5000/api/v1/health/system"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s --max-time 10 "$endpoint" > /dev/null 2>&1; then
            log "$endpoint - OK"
        else
            error "$endpoint - FAILED"
        fi
    done
    echo ""
}

# Function to check database status
check_database_status() {
    log "Checking database status..."
    
    echo -e "${CYAN}=== Database Status ===${NC}"
    
    # Check database size
    docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -d 3d_print_system -c "
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
    " 2>/dev/null || error "Could not get database table sizes"
    
    # Check active connections
    docker-compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -d 3d_print_system -c "
        SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';
    " 2>/dev/null || error "Could not get active connections"
    
    echo ""
}

# Function to check Redis status
check_redis_status() {
    log "Checking Redis status..."
    
    echo -e "${CYAN}=== Redis Status ===${NC}"
    
    # Check Redis info
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli info server 2>/dev/null | grep -E "(redis_version|uptime_in_seconds|connected_clients)" || \
        error "Could not get Redis server info"
    
    # Check Redis memory usage
    docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli info memory 2>/dev/null | grep -E "(used_memory_human|used_memory_peak_human)" || \
        error "Could not get Redis memory info"
    
    echo ""
}

# Function to check worker status
check_worker_status() {
    log "Checking worker status..."
    
    echo -e "${CYAN}=== Worker Status ===${NC}"
    
    # Check RQ info
    docker-compose -f "$COMPOSE_FILE" exec -T worker rq info 2>/dev/null || \
        error "Could not get RQ info"
    
    echo ""
}

# Function to show comprehensive status
show_comprehensive_status() {
    log "Showing comprehensive system status..."
    
    echo -e "${PURPLE}========================================${NC}"
    echo -e "${PURPLE}    3D Print Management System Status${NC}"
    echo -e "${PURPLE}========================================${NC}"
    echo ""
    
    # Check Docker Compose status
    check_compose_status || exit 1
    
    echo -e "${CYAN}=== Service Status ===${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Check each service health
    for service in "${services[@]}"; do
        check_service_health "$service"
    done
    echo ""
    
    # Check resource usage
    check_resource_usage
    
    # Check network connectivity
    check_network_connectivity
    
    # Check API endpoints
    check_api_endpoints
    
    # Check database status
    check_database_status
    
    # Check Redis status
    check_redis_status
    
    # Check worker status
    check_worker_status
}

# Function to show service logs
show_service_logs() {
    local service=$1
    local lines=${2:-100}
    
    if [ -z "$service" ]; then
        error "Please specify a service name"
        echo "Available services: ${services[*]}"
        exit 1
    fi
    
    get_service_logs "$service" "$lines"
}

# Function to show all logs
show_all_logs() {
    local lines=${1:-50}
    
    log "Showing logs for all services..."
    
    for service in "${services[@]}"; do
        get_service_logs "$service" "$lines"
    done
}

# Function to restart service
restart_service() {
    local service=$1
    
    if [ -z "$service" ]; then
        error "Please specify a service name"
        echo "Available services: ${services[*]}"
        exit 1
    fi
    
    log "Restarting service: $service"
    docker-compose -f "$COMPOSE_FILE" restart "$service"
    
    # Wait for service to be healthy
    log "Waiting for service to be healthy..."
    sleep 10
    
    check_service_health "$service"
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  status              Show comprehensive system status"
    echo "  logs [SERVICE]      Show logs for a specific service or all services"
    echo "  restart [SERVICE]   Restart a specific service"
    echo "  health [SERVICE]    Check health of a specific service"
    echo "  resources           Show resource usage"
    echo "  network             Check network connectivity"
    echo "  api                 Check API endpoints"
    echo "  help                Show this help message"
    echo ""
    echo "Services: ${services[*]}"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Show comprehensive status"
    echo "  $0 logs backend              # Show backend logs"
    echo "  $0 logs                      # Show all service logs"
    echo "  $0 restart frontend          # Restart frontend service"
    echo "  $0 health backend            # Check backend health"
}

# Main function
main() {
    local command=${1:-status}
    local service=$2
    local lines=$3
    
    case $command in
        "status")
            show_comprehensive_status
            ;;
        "logs")
            if [ -z "$service" ]; then
                show_all_logs "$lines"
            else
                show_service_logs "$service" "$lines"
            fi
            ;;
        "restart")
            restart_service "$service"
            ;;
        "health")
            if [ -z "$service" ]; then
                error "Please specify a service name"
                echo "Available services: ${services[*]}"
                exit 1
            fi
            check_service_health "$service"
            ;;
        "resources")
            check_resource_usage
            ;;
        "network")
            check_network_connectivity
            ;;
        "api")
            check_api_endpoints
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
