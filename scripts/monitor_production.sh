#!/bin/bash

# Comprehensive Production Monitoring Script for 3D Print Management System
# Provides real-time monitoring, alerting, and reporting capabilities

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
ALERT_LOG="$LOG_DIR/alerts.log"
METRICS_LOG="$LOG_DIR/metrics.log"
HEALTH_LOG="$LOG_DIR/health.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Alert thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
ERROR_RATE_THRESHOLD=5
RESPONSE_TIME_THRESHOLD=1000

# Function to log messages with timestamp
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_DIR/monitoring.log"
}

# Function to send alerts
send_alert() {
    local severity="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log alert
    echo "[$timestamp] [$severity] $message" >> "$ALERT_LOG"
    
    # Color-coded console output
    case $severity in
        "CRITICAL")
            echo -e "${RED}[$timestamp] CRITICAL: $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] WARNING: $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}[$timestamp] INFO: $message${NC}"
            ;;
        *)
            echo -e "${CYAN}[$timestamp] $severity: $message${NC}"
            ;;
    esac
    
    # TODO: Add email/SMS alerting here
    # Example: curl -X POST "https://api.example.com/alerts" -d "message=$message&severity=$severity"
}

# Function to check Docker services
check_docker_services() {
    log_message "INFO" "Checking Docker services..."
    
    local services=("backend" "frontend" "db" "redis" "worker")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*healthy"; then
            log_message "INFO" "Service $service is healthy"
        elif docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service"; then
            log_message "WARNING" "Service $service is running but not healthy"
            all_healthy=false
        else
            log_message "CRITICAL" "Service $service is not running"
            send_alert "CRITICAL" "Service $service is not running"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_message "INFO" "All Docker services are healthy"
    else
        log_message "WARNING" "Some Docker services have issues"
    fi
}

# Function to check system resources
check_system_resources() {
    log_message "INFO" "Checking system resources..."
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local cpu_usage_int=${cpu_usage%.*}
    
    if [ "$cpu_usage_int" -gt "$CPU_THRESHOLD" ]; then
        send_alert "WARNING" "High CPU usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    local memory_info=$(free | grep Mem)
    local memory_total=$(echo $memory_info | awk '{print $2}')
    local memory_used=$(echo $memory_info | awk '{print $3}')
    local memory_percent=$((memory_used * 100 / memory_total))
    
    if [ "$memory_percent" -gt "$MEMORY_THRESHOLD" ]; then
        send_alert "WARNING" "High memory usage: ${memory_percent}%"
    fi
    
    # Disk usage
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        send_alert "CRITICAL" "High disk usage: ${disk_usage}%"
    fi
    
    # Log metrics
    echo "$(date '+%Y-%m-%d %H:%M:%S'),cpu:$cpu_usage,memory:$memory_percent,disk:$disk_usage" >> "$METRICS_LOG"
}

# Function to check application health
check_application_health() {
    log_message "INFO" "Checking application health..."
    
    local health_url="http://localhost:5000/api/v1/monitoring/health"
    local status_url="http://localhost:5000/api/v1/monitoring/status"
    local ping_url="http://localhost:5000/api/v1/monitoring/ping"
    
    # Check ping endpoint
    if curl -f -s "$ping_url" > /dev/null; then
        log_message "INFO" "Application ping successful"
    else
        send_alert "CRITICAL" "Application ping failed"
        return 1
    fi
    
    # Check status endpoint
    local status_response=$(curl -s "$status_url" 2>/dev/null || echo '{"status":"unhealthy"}')
    local app_status=$(echo "$status_response" | jq -r '.status' 2>/dev/null || echo "unknown")
    
    if [ "$app_status" = "healthy" ]; then
        log_message "INFO" "Application status: healthy"
    elif [ "$app_status" = "degraded" ]; then
        log_message "WARNING" "Application status: degraded"
        send_alert "WARNING" "Application is in degraded state"
    else
        log_message "CRITICAL" "Application status: $app_status"
        send_alert "CRITICAL" "Application is unhealthy: $app_status"
    fi
    
    # Check comprehensive health
    local health_response=$(curl -s "$health_url" 2>/dev/null || echo '{}')
    local overall_health=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")
    
    if [ "$overall_health" != "healthy" ]; then
        # Check component health
        local components=$(echo "$health_response" | jq -r '.health_checks | to_entries[] | "\(.key):\(.value)"' 2>/dev/null || echo "")
        for component in $components; do
            local comp_name=$(echo "$component" | cut -d':' -f1)
            local comp_status=$(echo "$component" | cut -d':' -f2)
            if [ "$comp_status" != "healthy" ]; then
                send_alert "WARNING" "Component $comp_name is $comp_status"
            fi
        done
    fi
    
    # Log health status
    echo "$(date '+%Y-%m-%d %H:%M:%S'),app_status:$app_status,overall_health:$overall_health" >> "$HEALTH_LOG"
}

# Function to check performance metrics
check_performance_metrics() {
    log_message "INFO" "Checking performance metrics..."
    
    local metrics_url="http://localhost:5000/api/v1/monitoring/metrics/application"
    local alerts_url="http://localhost:5000/api/v1/monitoring/alerts"
    
    # Get application metrics
    local metrics_response=$(curl -s "$metrics_url" 2>/dev/null || echo '{}')
    local error_rate=$(echo "$metrics_response" | jq -r '.requests.error_rate_percent' 2>/dev/null || echo "0")
    local total_requests=$(echo "$metrics_response" | jq -r '.requests.total' 2>/dev/null || echo "0")
    local total_errors=$(echo "$metrics_response" | jq -r '.requests.errors' 2>/dev/null || echo "0")
    
    # Check error rate
    local error_rate_int=${error_rate%.*}
    if [ "$error_rate_int" -gt "$ERROR_RATE_THRESHOLD" ]; then
        send_alert "CRITICAL" "High error rate: ${error_rate}% (${total_errors} errors out of ${total_requests} requests)"
    fi
    
    # Check slow endpoints
    local slow_endpoints=$(echo "$metrics_response" | jq -r '.performance.slow_endpoints[] | "\(.path):\(.avg_duration_ms)"' 2>/dev/null || echo "")
    for endpoint in $slow_endpoints; do
        local path=$(echo "$endpoint" | cut -d':' -f1)
        local duration=$(echo "$endpoint" | cut -d':' -f2)
        local duration_int=${duration%.*}
        if [ "$duration_int" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            send_alert "WARNING" "Slow endpoint detected: $path (${duration}ms avg)"
        fi
    done
    
    # Get performance alerts
    local alerts_response=$(curl -s "$alerts_url" 2>/dev/null || echo '{"alerts":[]}')
    local alert_count=$(echo "$alerts_response" | jq -r '.count' 2>/dev/null || echo "0")
    
    if [ "$alert_count" -gt 0 ]; then
        local critical_alerts=$(echo "$alerts_response" | jq -r '.alerts[] | select(.severity=="critical") | .message' 2>/dev/null || echo "")
        for alert in $critical_alerts; do
            send_alert "CRITICAL" "Performance alert: $alert"
        done
    fi
}

# Function to check database health
check_database_health() {
    log_message "INFO" "Checking database health..."
    
    local db_metrics_url="http://localhost:5000/api/v1/monitoring/metrics/database"
    local db_response=$(curl -s "$db_metrics_url" 2>/dev/null || echo '{}')
    local db_status=$(echo "$db_response" | jq -r '.connectivity.status' 2>/dev/null || echo "unknown")
    local db_response_time=$(echo "$db_response" | jq -r '.connectivity.response_time_ms' 2>/dev/null || echo "0")
    
    if [ "$db_status" != "healthy" ]; then
        send_alert "CRITICAL" "Database is unhealthy: $db_status"
    fi
    
    # Check response time
    local response_time_int=${db_response_time%.*}
    if [ "$response_time_int" -gt 100 ]; then
        send_alert "WARNING" "Slow database response: ${db_response_time}ms"
    fi
    
    # Check table sizes
    local job_count=$(echo "$db_response" | jq -r '.tables.jobs' 2>/dev/null || echo "0")
    local event_count=$(echo "$db_response" | jq -r '.tables.events' 2>/dev/null || echo "0")
    
    if [ "$job_count" -gt 10000 ]; then
        send_alert "WARNING" "Large number of jobs in database: $job_count"
    fi
    
    if [ "$event_count" -gt 50000 ]; then
        send_alert "WARNING" "Large number of events in database: $event_count"
    fi
}

# Function to check storage health
check_storage_health() {
    log_message "INFO" "Checking storage health..."
    
    local storage_metrics_url="http://localhost:5000/api/v1/monitoring/metrics/storage"
    local storage_response=$(curl -s "$storage_metrics_url" 2>/dev/null || echo '{}')
    local storage_status=$(echo "$storage_response" | jq -r '.status' 2>/dev/null || echo "unknown")
    local storage_usage=$(echo "$storage_response" | jq -r '.disk.percent_used' 2>/dev/null || echo "0")
    
    if [ "$storage_status" != "healthy" ]; then
        send_alert "CRITICAL" "Storage is unhealthy: $storage_status"
    fi
    
    # Check storage usage
    local storage_usage_int=${storage_usage%.*}
    if [ "$storage_usage_int" -gt "$DISK_THRESHOLD" ]; then
        send_alert "CRITICAL" "High storage usage: ${storage_usage}%"
    fi
    
    # Check file count
    local file_count=$(echo "$storage_response" | jq -r '.files.count' 2>/dev/null || echo "0")
    if [ "$file_count" -gt 10000 ]; then
        send_alert "WARNING" "Large number of files in storage: $file_count"
    fi
}

# Function to generate monitoring report
generate_report() {
    local report_file="$LOG_DIR/monitoring_report_$(date '+%Y%m%d_%H%M%S').txt"
    
    log_message "INFO" "Generating monitoring report..."
    
    {
        echo "=== 3D Print Management System - Monitoring Report ==="
        echo "Generated: $(date)"
        echo "=================================================="
        echo ""
        
        echo "=== System Resources ==="
        echo "CPU Usage: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1)%"
        echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
        echo "Disk Usage: $(df / | tail -1 | awk '{print $5}')"
        echo ""
        
        echo "=== Docker Services ==="
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "=== Application Health ==="
        curl -s "http://localhost:5000/api/v1/monitoring/status" | jq '.' 2>/dev/null || echo "Unable to fetch application status"
        echo ""
        
        echo "=== Recent Alerts ==="
        tail -20 "$ALERT_LOG" 2>/dev/null || echo "No alerts found"
        echo ""
        
        echo "=== Performance Metrics ==="
        curl -s "http://localhost:5000/api/v1/monitoring/metrics/application" | jq '.' 2>/dev/null || echo "Unable to fetch performance metrics"
        echo ""
        
        echo "=== Database Metrics ==="
        curl -s "http://localhost:5000/api/v1/monitoring/metrics/database" | jq '.' 2>/dev/null || echo "Unable to fetch database metrics"
        echo ""
        
        echo "=== Storage Metrics ==="
        curl -s "http://localhost:5000/api/v1/monitoring/metrics/storage" | jq '.' 2>/dev/null || echo "Unable to fetch storage metrics"
        
    } > "$report_file"
    
    log_message "INFO" "Monitoring report generated: $report_file"
    echo -e "${GREEN}Monitoring report generated: $report_file${NC}"
}

# Function to show monitoring dashboard
show_dashboard() {
    clear
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}    3D Print Management System Monitor${NC}"
    echo -e "${CYAN}================================================${NC}"
    echo ""
    
    # System resources
    echo -e "${BLUE}System Resources:${NC}"
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local memory_percent=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df / | tail -1 | awk '{print $5}')
    
    echo "  CPU: ${cpu_usage}%"
    echo "  Memory: ${memory_percent}%"
    echo "  Disk: ${disk_usage}"
    echo ""
    
    # Docker services
    echo -e "${BLUE}Docker Services:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}" | while read line; do
        if [[ $line == *"healthy"* ]]; then
            echo -e "  ${GREEN}✓${NC} $line"
        elif [[ $line == *"Up"* ]]; then
            echo -e "  ${YELLOW}⚠${NC} $line"
        else
            echo -e "  ${RED}✗${NC} $line"
        fi
    done
    echo ""
    
    # Application status
    echo -e "${BLUE}Application Status:${NC}"
    local status_response=$(curl -s "http://localhost:5000/api/v1/monitoring/status" 2>/dev/null || echo '{"status":"unknown"}')
    local app_status=$(echo "$status_response" | jq -r '.status' 2>/dev/null || echo "unknown")
    
    case $app_status in
        "healthy")
            echo -e "  ${GREEN}✓ Application: Healthy${NC}"
            ;;
        "degraded")
            echo -e "  ${YELLOW}⚠ Application: Degraded${NC}"
            ;;
        *)
            echo -e "  ${RED}✗ Application: $app_status${NC}"
            ;;
    esac
    echo ""
    
    # Recent alerts
    echo -e "${BLUE}Recent Alerts:${NC}"
    if [ -f "$ALERT_LOG" ]; then
        tail -5 "$ALERT_LOG" | while read line; do
            if [[ $line == *"CRITICAL"* ]]; then
                echo -e "  ${RED}$line${NC}"
            elif [[ $line == *"WARNING"* ]]; then
                echo -e "  ${YELLOW}$line${NC}"
            else
                echo -e "  ${BLUE}$line${NC}"
            fi
        done
    else
        echo "  No alerts found"
    fi
    echo ""
    
    echo -e "${CYAN}Press Ctrl+C to exit${NC}"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -c, --check         Run a single health check"
    echo "  -d, --dashboard     Show real-time monitoring dashboard"
    echo "  -r, --report        Generate monitoring report"
    echo "  -w, --watch         Run continuous monitoring"
    echo "  -i, --interval SEC  Set monitoring interval in seconds (default: 30)"
    echo ""
    echo "Examples:"
    echo "  $0 --check          Run one-time health check"
    echo "  $0 --dashboard      Show monitoring dashboard"
    echo "  $0 --watch          Run continuous monitoring"
    echo "  $0 --watch --interval 60  Run monitoring every 60 seconds"
}

# Main monitoring function
run_monitoring() {
    local interval=${1:-30}
    
    log_message "INFO" "Starting monitoring with ${interval}s interval"
    send_alert "INFO" "Monitoring started"
    
    while true; do
        log_message "INFO" "Running monitoring cycle..."
        
        check_docker_services
        check_system_resources
        check_application_health
        check_performance_metrics
        check_database_health
        check_storage_health
        
        log_message "INFO" "Monitoring cycle completed"
        
        sleep "$interval"
    done
}

# Main script logic
case "${1:-}" in
    -h|--help)
        show_help
        ;;
    -c|--check)
        log_message "INFO" "Running single health check..."
        check_docker_services
        check_system_resources
        check_application_health
        check_performance_metrics
        check_database_health
        check_storage_health
        log_message "INFO" "Health check completed"
        ;;
    -d|--dashboard)
        show_dashboard
        ;;
    -r|--report)
        generate_report
        ;;
    -w|--watch)
        local interval=30
        if [ "$2" = "--interval" ] || [ "$2" = "-i" ]; then
            interval="$3"
        fi
        run_monitoring "$interval"
        ;;
    -i|--interval)
        if [ -n "$2" ]; then
            run_monitoring "$2"
        else
            echo "Error: No interval specified"
            show_help
            exit 1
        fi
        ;;
    "")
        # Default: run single check
        log_message "INFO" "Running single health check..."
        check_docker_services
        check_system_resources
        check_application_health
        check_performance_metrics
        check_database_health
        check_storage_health
        log_message "INFO" "Health check completed"
        ;;
    *)
        echo "Error: Unknown option $1"
        show_help
        exit 1
        ;;
esac
