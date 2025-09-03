#!/bin/bash
# SSL Certificate Setup Script for 3D Print Management System
# This script helps set up SSL certificates using Let's Encrypt or custom certificates

set -e

# Configuration
DOMAIN=${DOMAIN_NAME:-"localhost"}
EMAIL=${SSL_EMAIL:-"admin@${DOMAIN}"}
SSL_DIR="/etc/ssl"
CERT_DIR="${SSL_DIR}/certs"
PRIVATE_DIR="${SSL_DIR}/private"
LETSENCRYPT_DIR="/etc/letsencrypt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating SSL directories..."
    mkdir -p "${CERT_DIR}"
    mkdir -p "${PRIVATE_DIR}"
    chmod 755 "${CERT_DIR}"
    chmod 700 "${PRIVATE_DIR}"
}

# Generate self-signed certificate for development/testing
generate_self_signed() {
    log_info "Generating self-signed certificate for ${DOMAIN}..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "${PRIVATE_DIR}/${DOMAIN}.key" \
        -out "${CERT_DIR}/${DOMAIN}.crt" \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=${DOMAIN}/emailAddress=${EMAIL}"
    
    chmod 600 "${PRIVATE_DIR}/${DOMAIN}.key"
    chmod 644 "${CERT_DIR}/${DOMAIN}.crt"
    
    log_info "Self-signed certificate generated successfully"
    log_warn "Self-signed certificates are for development only!"
}

# Setup Let's Encrypt certificate
setup_letsencrypt() {
    log_info "Setting up Let's Encrypt certificate for ${DOMAIN}..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        log_info "Installing certbot..."
        if command -v apt-get &> /dev/null; then
            apt-get update
            apt-get install -y certbot
        elif command -v yum &> /dev/null; then
            yum install -y certbot
        else
            log_error "Package manager not supported. Please install certbot manually."
            exit 1
        fi
    fi
    
    # Create webroot directory
    mkdir -p /var/www/certbot
    
    # Generate certificate
    log_info "Requesting certificate from Let's Encrypt..."
    certbot certonly --webroot \
        -w /var/www/certbot \
        -d "${DOMAIN}" \
        --email "${EMAIL}" \
        --agree-tos \
        --non-interactive \
        --expand
    
    # Create symbolic links to certificates
    ln -sf "${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem" "${CERT_DIR}/${DOMAIN}.crt"
    ln -sf "${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem" "${PRIVATE_DIR}/${DOMAIN}.key"
    
    log_info "Let's Encrypt certificate installed successfully"
    
    # Setup auto-renewal
    setup_auto_renewal
}

# Setup automatic certificate renewal
setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /etc/cron.daily/ssl-renew << 'EOF'
#!/bin/bash
# Automatic SSL certificate renewal
/usr/bin/certbot renew --quiet --pre-hook "docker-compose -f /opt/3d-print-system/docker-compose.prod.yml stop nginx" --post-hook "docker-compose -f /opt/3d-print-system/docker-compose.prod.yml start nginx"
EOF
    
    chmod +x /etc/cron.daily/ssl-renew
    log_info "Auto-renewal configured successfully"
}

# Install custom certificate
install_custom() {
    if [ -z "${CERT_FILE}" ] || [ -z "${KEY_FILE}" ]; then
        log_error "Please provide CERT_FILE and KEY_FILE environment variables for custom certificates"
        exit 1
    fi
    
    if [ ! -f "${CERT_FILE}" ] || [ ! -f "${KEY_FILE}" ]; then
        log_error "Certificate or key file not found"
        exit 1
    fi
    
    log_info "Installing custom certificate..."
    
    cp "${CERT_FILE}" "${CERT_DIR}/${DOMAIN}.crt"
    cp "${KEY_FILE}" "${PRIVATE_DIR}/${DOMAIN}.key"
    
    chmod 644 "${CERT_DIR}/${DOMAIN}.crt"
    chmod 600 "${PRIVATE_DIR}/${DOMAIN}.key"
    
    log_info "Custom certificate installed successfully"
}

# Verify certificate
verify_certificate() {
    log_info "Verifying certificate for ${DOMAIN}..."
    
    if [ ! -f "${CERT_DIR}/${DOMAIN}.crt" ] || [ ! -f "${PRIVATE_DIR}/${DOMAIN}.key" ]; then
        log_error "Certificate files not found"
        exit 1
    fi
    
    # Check certificate validity
    openssl x509 -in "${CERT_DIR}/${DOMAIN}.crt" -text -noout > /dev/null
    if [ $? -eq 0 ]; then
        log_info "Certificate is valid"
        
        # Show certificate info
        echo "Certificate Information:"
        openssl x509 -in "${CERT_DIR}/${DOMAIN}.crt" -subject -dates -noout
    else
        log_error "Certificate is invalid"
        exit 1
    fi
    
    # Check key format
    openssl rsa -in "${PRIVATE_DIR}/${DOMAIN}.key" -check -noout > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "Private key is valid"
    else
        log_error "Private key is invalid"
        exit 1
    fi
}

# Main function
main() {
    check_root
    create_directories
    
    case "${1:-}" in
        "letsencrypt")
            setup_letsencrypt
            ;;
        "self-signed")
            generate_self_signed
            ;;
        "custom")
            install_custom
            ;;
        "verify")
            verify_certificate
            ;;
        "renew")
            log_info "Renewing Let's Encrypt certificate..."
            certbot renew --force-renewal
            ;;
        *)
            echo "Usage: $0 {letsencrypt|self-signed|custom|verify|renew}"
            echo ""
            echo "Environment variables:"
            echo "  DOMAIN_NAME  - Domain name for certificate (default: localhost)"
            echo "  SSL_EMAIL    - Email for Let's Encrypt (default: admin@domain)"
            echo "  CERT_FILE    - Path to certificate file (for custom option)"
            echo "  KEY_FILE     - Path to private key file (for custom option)"
            echo ""
            echo "Examples:"
            echo "  DOMAIN_NAME=example.com SSL_EMAIL=admin@example.com $0 letsencrypt"
            echo "  $0 self-signed"
            echo "  CERT_FILE=/path/to/cert.pem KEY_FILE=/path/to/key.pem $0 custom"
            exit 1
            ;;
    esac
    
    verify_certificate
    log_info "SSL setup completed successfully!"
    log_info "Certificate: ${CERT_DIR}/${DOMAIN}.crt"
    log_info "Private Key: ${PRIVATE_DIR}/${DOMAIN}.key"
}

main "$@"
