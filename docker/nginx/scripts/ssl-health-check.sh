#!/bin/bash
# SSL Health Check Script for 3D Print Management System
# This script monitors SSL certificate health and expiration

set -e

# Configuration
DOMAIN=${DOMAIN_NAME:-"localhost"}
PORT=${SSL_PORT:-443}
WARNING_DAYS=${SSL_WARNING_DAYS:-30}
CRITICAL_DAYS=${SSL_CRITICAL_DAYS:-7}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check SSL certificate expiration
check_cert_expiration() {
    log_info "Checking SSL certificate expiration for ${DOMAIN}:${PORT}..."
    
    # Get certificate expiration date
    local cert_info
    cert_info=$(echo | timeout 10 openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:${PORT}" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to retrieve certificate information"
        return 1
    fi
    
    local expiry_date
    expiry_date=$(echo "${cert_info}" | grep 'notAfter' | cut -d= -f2)
    
    if [ -z "${expiry_date}" ]; then
        log_error "Could not extract certificate expiration date"
        return 1
    fi
    
    log_debug "Certificate expires: ${expiry_date}"
    
    # Convert expiry date to epoch
    local expiry_epoch
    expiry_epoch=$(date -d "${expiry_date}" +%s 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to parse expiration date"
        return 1
    fi
    
    # Calculate days until expiration
    local current_epoch
    current_epoch=$(date +%s)
    local days_until_expiry
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    log_info "Certificate expires in ${days_until_expiry} days"
    
    # Check expiration status
    if [ ${days_until_expiry} -le ${CRITICAL_DAYS} ]; then
        log_error "CRITICAL: Certificate expires in ${days_until_expiry} days!"
        return 2
    elif [ ${days_until_expiry} -le ${WARNING_DAYS} ]; then
        log_warn "WARNING: Certificate expires in ${days_until_expiry} days"
        return 1
    else
        log_info "Certificate expiration is healthy (${days_until_expiry} days)"
        return 0
    fi
}

# Check SSL certificate validity
check_cert_validity() {
    log_info "Checking SSL certificate validity for ${DOMAIN}:${PORT}..."
    
    # Check if we can establish SSL connection
    if ! echo | timeout 10 openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:${PORT}" >/dev/null 2>&1; then
        log_error "Failed to establish SSL connection to ${DOMAIN}:${PORT}"
        return 1
    fi
    
    # Get certificate details
    local cert_details
    cert_details=$(echo | timeout 10 openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:${PORT}" 2>/dev/null | openssl x509 -text -noout 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to retrieve certificate details"
        return 1
    fi
    
    # Check certificate subject
    local cert_subject
    cert_subject=$(echo "${cert_details}" | grep "Subject:" | head -1)
    log_debug "Certificate subject: ${cert_subject}"
    
    # Check if certificate matches domain
    local cert_san
    cert_san=$(echo "${cert_details}" | grep -A1 "Subject Alternative Name" | tail -1 | tr ',' '\n' | grep "DNS:" | sed 's/.*DNS://')
    
    if echo "${cert_san}" | grep -q "${DOMAIN}"; then
        log_info "Certificate domain validation successful"
    else
        log_warn "Certificate may not match domain ${DOMAIN}"
    fi
    
    log_info "SSL certificate is valid"
    return 0
}

# Check SSL protocol and cipher strength
check_ssl_strength() {
    log_info "Checking SSL protocol and cipher strength for ${DOMAIN}:${PORT}..."
    
    # Check supported protocols
    local ssl_info
    ssl_info=$(echo | timeout 10 openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:${PORT}" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to retrieve SSL protocol information"
        return 1
    fi
    
    # Extract protocol version
    local protocol
    protocol=$(echo "${ssl_info}" | grep "Protocol" | head -1 | awk '{print $3}')
    log_debug "SSL Protocol: ${protocol}"
    
    # Extract cipher suite
    local cipher
    cipher=$(echo "${ssl_info}" | grep "Cipher" | head -1 | awk '{print $3}')
    log_debug "Cipher Suite: ${cipher}"
    
    # Check for weak protocols
    case "${protocol}" in
        "TLSv1.3"|"TLSv1.2")
            log_info "SSL protocol ${protocol} is secure"
            ;;
        "TLSv1.1"|"TLSv1")
            log_warn "SSL protocol ${protocol} is deprecated"
            ;;
        "SSLv3"|"SSLv2")
            log_error "SSL protocol ${protocol} is insecure"
            return 1
            ;;
        *)
            log_warn "Unknown SSL protocol: ${protocol}"
            ;;
    esac
    
    return 0
}

# Check HSTS header
check_hsts() {
    log_info "Checking HSTS (HTTP Strict Transport Security) header..."
    
    local hsts_header
    hsts_header=$(curl -s -I -m 10 "https://${DOMAIN}/" | grep -i "strict-transport-security" | head -1)
    
    if [ -n "${hsts_header}" ]; then
        log_info "HSTS header present: ${hsts_header}"
        return 0
    else
        log_warn "HSTS header not found - consider enabling for enhanced security"
        return 1
    fi
}

# Check certificate chain
check_cert_chain() {
    log_info "Checking SSL certificate chain for ${DOMAIN}:${PORT}..."
    
    # Verify certificate chain
    local chain_check
    chain_check=$(echo | timeout 10 openssl s_client -servername "${DOMAIN}" -connect "${DOMAIN}:${PORT}" -verify_return_error 2>&1)
    
    if echo "${chain_check}" | grep -q "Verify return code: 0 (ok)"; then
        log_info "Certificate chain is valid"
        return 0
    else
        log_error "Certificate chain validation failed"
        log_debug "${chain_check}"
        return 1
    fi
}

# Generate health report
generate_report() {
    local exit_code=0
    
    echo "============================================="
    echo "SSL Health Check Report for ${DOMAIN}:${PORT}"
    echo "Generated: $(date)"
    echo "============================================="
    echo ""
    
    # Run all checks
    check_cert_validity || exit_code=$((exit_code + 1))
    echo ""
    
    check_cert_expiration || exit_code=$((exit_code + 1))
    echo ""
    
    check_ssl_strength || exit_code=$((exit_code + 1))
    echo ""
    
    check_hsts || true  # Don't fail on missing HSTS
    echo ""
    
    check_cert_chain || exit_code=$((exit_code + 1))
    echo ""
    
    echo "============================================="
    if [ ${exit_code} -eq 0 ]; then
        log_info "SSL health check PASSED"
    else
        log_error "SSL health check FAILED with ${exit_code} issues"
    fi
    echo "============================================="
    
    return ${exit_code}
}

# Monitor mode - run continuously
monitor_mode() {
    log_info "Starting SSL monitoring for ${DOMAIN}:${PORT}..."
    log_info "Check interval: ${MONITOR_INTERVAL:-300} seconds"
    
    while true; do
        if generate_report; then
            log_info "SSL health check passed - sleeping..."
        else
            log_error "SSL health check failed - alerting..."
            # Here you could add alerting logic (email, webhook, etc.)
        fi
        
        sleep "${MONITOR_INTERVAL:-300}"
    done
}

# Main function
main() {
    case "${1:-check}" in
        "check"|"")
            generate_report
            ;;
        "expiration")
            check_cert_expiration
            ;;
        "validity")
            check_cert_validity
            ;;
        "strength")
            check_ssl_strength
            ;;
        "hsts")
            check_hsts
            ;;
        "chain")
            check_cert_chain
            ;;
        "monitor")
            monitor_mode
            ;;
        *)
            echo "Usage: $0 {check|expiration|validity|strength|hsts|chain|monitor}"
            echo ""
            echo "Environment variables:"
            echo "  DOMAIN_NAME        - Domain to check (default: localhost)"
            echo "  SSL_PORT           - Port to check (default: 443)"
            echo "  SSL_WARNING_DAYS   - Warning threshold in days (default: 30)"
            echo "  SSL_CRITICAL_DAYS  - Critical threshold in days (default: 7)"
            echo "  MONITOR_INTERVAL   - Monitoring interval in seconds (default: 300)"
            echo ""
            echo "Examples:"
            echo "  DOMAIN_NAME=example.com $0 check"
            echo "  $0 expiration"
            echo "  MONITOR_INTERVAL=60 $0 monitor"
            exit 1
            ;;
    esac
}

main "$@"
