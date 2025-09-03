# SSL/TLS Configuration Guide

This guide provides comprehensive instructions for setting up SSL/TLS encryption for the 3D Print Management System using nginx as a reverse proxy.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [SSL Certificate Options](#ssl-certificate-options)
4. [Development Setup](#development-setup)
5. [Production Setup](#production-setup)
6. [Let's Encrypt Setup](#lets-encrypt-setup)
7. [Custom Certificate Setup](#custom-certificate-setup)
8. [Health Monitoring](#health-monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

## Overview

The SSL/TLS configuration implements:

- **nginx reverse proxy** for SSL termination
- **Automatic HTTP → HTTPS redirection**
- **Security headers** for enhanced protection
- **Let's Encrypt integration** for free SSL certificates
- **Automated certificate renewal**
- **SSL health monitoring** and alerting

### Architecture

```
Internet → nginx (SSL termination) → Backend/Frontend (internal HTTP)
```

- All external traffic uses HTTPS (port 443)
- nginx handles SSL termination and forwards to internal services
- Backend and frontend communicate via internal HTTP (secure within Docker network)

## Prerequisites

### System Requirements

- Docker and Docker Compose installed
- Domain name pointing to your server (for production)
- Firewall configured to allow ports 80 and 443
- Valid email address for Let's Encrypt (production)

### DNS Configuration

For production deployment, ensure your domain points to your server:

```bash
# Check DNS resolution
nslookup yourdomain.com

# Should return your server's IP address
```

## SSL Certificate Options

### 1. Self-Signed Certificates (Development)

- **Use Case**: Development and testing
- **Security**: Not trusted by browsers (warning shown)
- **Setup**: Automatic generation
- **Cost**: Free

### 2. Let's Encrypt (Production - Recommended)

- **Use Case**: Production deployments
- **Security**: Trusted by all browsers
- **Setup**: Automated with certbot
- **Cost**: Free
- **Limitations**: Rate limits, domain validation required

### 3. Custom Certificates (Enterprise)

- **Use Case**: Enterprise environments with existing CA
- **Security**: Depends on CA
- **Setup**: Manual certificate installation
- **Cost**: Varies

## Development Setup

### Step 1: Configure Environment

```bash
# Edit .env file
DOMAIN_NAME=localhost
SSL_TYPE=self-signed
SSL_EMAIL=admin@localhost
FRONTEND_PUBLIC_URL=https://localhost
NEXT_PUBLIC_API_URL=https://localhost/api
```

### Step 2: Generate Self-Signed Certificate

```bash
# Create SSL directories
mkdir -p docker/ssl/certs docker/ssl/private

# Generate self-signed certificate
docker run --rm -v $(pwd)/docker/ssl:/ssl \
    -e DOMAIN_NAME=localhost \
    -e SSL_EMAIL=admin@localhost \
    alpine/ssl-tools:latest sh -c "
    chmod +x /ssl/setup-ssl.sh && 
    /ssl/setup-ssl.sh self-signed
"

# Or use the setup script directly
chmod +x docker/nginx/scripts/setup-ssl.sh
sudo docker/nginx/scripts/setup-ssl.sh self-signed
```

### Step 3: Start with SSL

```bash
# Start all services with nginx
docker-compose -f docker-compose.prod.yml up -d

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Step 4: Test HTTPS Access

```bash
# Test HTTPS (ignore certificate warning for self-signed)
curl -k https://localhost/health

# Access in browser (accept security warning)
# https://localhost
```

## Production Setup

### Step 1: Configure Production Environment

```bash
# Edit .env file for production
DOMAIN_NAME=yourdomain.com
SSL_TYPE=letsencrypt
SSL_EMAIL=admin@yourdomain.com
FRONTEND_PUBLIC_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
FLASK_ENV=production
NODE_ENV=production
```

### Step 2: Prepare SSL Directory Structure

```bash
# Create SSL directories
sudo mkdir -p /etc/ssl/certs /etc/ssl/private
sudo chmod 755 /etc/ssl/certs
sudo chmod 700 /etc/ssl/private

# Create Let's Encrypt directories
sudo mkdir -p /etc/letsencrypt /var/www/certbot
sudo chmod 755 /etc/letsencrypt /var/www/certbot
```

### Step 3: Initial Certificate Generation

You have two options for initial setup:

#### Option A: Staging Setup (Recommended for Testing)

```bash
# Start without SSL first to get Let's Encrypt certificate
# Temporarily serve HTTP challenge
docker run --rm -d -p 80:80 -v /var/www/certbot:/usr/share/nginx/html:ro nginx:alpine

# Generate staging certificate first
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --non-interactive \
    --staging

# Stop temporary nginx
docker stop $(docker ps -q --filter ancestor=nginx:alpine)
```

#### Option B: Direct Production

```bash
# Generate production certificate
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --non-interactive
```

### Step 4: Start Production Services

```bash
# Start all services with SSL profile
docker-compose -f docker-compose.prod.yml --profile ssl up -d

# Monitor startup logs
docker-compose -f docker-compose.prod.yml logs -f nginx certbot
```

### Step 5: Verify Production Setup

```bash
# Test SSL certificate
./docker/nginx/scripts/ssl-health-check.sh check

# Test HTTPS access
curl https://yourdomain.com/health

# Check certificate details
openssl s_client -servername yourdomain.com -connect yourdomain.com:443 -showcerts
```

## Let's Encrypt Setup

### Automatic Setup with Docker Compose

The production docker-compose configuration includes automatic Let's Encrypt setup:

```yaml
# Let's Encrypt is handled by certbot and ssl-renew services
# Configuration in docker-compose.prod.yml
```

### Manual Let's Encrypt Setup

If you prefer manual control:

```bash
# Install certbot
sudo apt install certbot -y

# Generate certificate
sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d yourdomain.com \
    --email admin@yourdomain.com \
    --agree-tos \
    --non-interactive

# Copy certificates to Docker volumes
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/ssl/certs/yourdomain.com.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/ssl/private/yourdomain.com.key

# Set permissions
sudo chmod 644 /path/to/ssl/certs/yourdomain.com.crt
sudo chmod 600 /path/to/ssl/private/yourdomain.com.key
```

### Certificate Renewal

Automatic renewal is configured via the `ssl-renew` service:

```bash
# Check renewal status
docker-compose -f docker-compose.prod.yml logs ssl-renew

# Manual renewal test
docker-compose -f docker-compose.prod.yml exec ssl-renew certbot renew --dry-run

# Force renewal
docker-compose -f docker-compose.prod.yml exec ssl-renew certbot renew --force-renewal
```

### Renewal Monitoring

```bash
# Check renewal cron job
sudo crontab -l | grep ssl

# Add custom renewal monitoring
echo "0 2 * * * /path/to/ssl-health-check.sh expiration && echo 'SSL check passed' || echo 'SSL check failed'" | sudo crontab -
```

## Custom Certificate Setup

### Step 1: Prepare Certificate Files

```bash
# Your certificate files should be in PEM format:
# - yourdomain.com.crt (certificate + intermediate chain)
# - yourdomain.com.key (private key)

# Verify certificate format
openssl x509 -in yourdomain.com.crt -text -noout
openssl rsa -in yourdomain.com.key -check -noout
```

### Step 2: Install Custom Certificates

```bash
# Copy certificates to SSL directory
sudo cp yourdomain.com.crt /etc/ssl/certs/
sudo cp yourdomain.com.key /etc/ssl/private/

# Set proper permissions
sudo chmod 644 /etc/ssl/certs/yourdomain.com.crt
sudo chmod 600 /etc/ssl/private/yourdomain.com.key

# Or use the setup script
CERT_FILE=yourdomain.com.crt KEY_FILE=yourdomain.com.key \
    sudo ./docker/nginx/scripts/setup-ssl.sh custom
```

### Step 3: Update Configuration

```bash
# Edit .env file
SSL_TYPE=custom
SSL_CERT_PATH=/etc/ssl/certs/yourdomain.com.crt
SSL_KEY_PATH=/etc/ssl/private/yourdomain.com.key
```

### Step 4: Restart Services

```bash
# Restart nginx to load new certificates
docker-compose -f docker-compose.prod.yml restart nginx

# Verify certificate
./docker/nginx/scripts/ssl-health-check.sh check
```

## Health Monitoring

### SSL Health Check Script

The system includes a comprehensive SSL health monitoring script:

```bash
# Run complete health check
./docker/nginx/scripts/ssl-health-check.sh check

# Check specific aspects
./docker/nginx/scripts/ssl-health-check.sh expiration
./docker/nginx/scripts/ssl-health-check.sh validity
./docker/nginx/scripts/ssl-health-check.sh strength
./docker/nginx/scripts/ssl-health-check.sh hsts
```

### Continuous Monitoring

```bash
# Start monitoring mode (runs continuously)
DOMAIN_NAME=yourdomain.com ./docker/nginx/scripts/ssl-health-check.sh monitor

# Configure monitoring interval (default: 5 minutes)
MONITOR_INTERVAL=300 ./docker/nginx/scripts/ssl-health-check.sh monitor
```

### Health Check Integration

Add SSL monitoring to your system monitoring:

```bash
# Add to crontab for regular checks
echo "*/30 * * * * /path/to/ssl-health-check.sh check || logger 'SSL health check failed'" | crontab -

# Integration with system monitoring
# Add to your monitoring system (Prometheus, Nagios, etc.)
```

## Troubleshooting

### Common Issues

#### 1. Certificate Not Found

```bash
# Check certificate files exist
ls -la /etc/ssl/certs/yourdomain.com.crt
ls -la /etc/ssl/private/yourdomain.com.key

# Check nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

#### 2. Let's Encrypt Rate Limits

```bash
# Check rate limit status
curl -s "https://crt.sh/?q=yourdomain.com&output=json" | jq '.[] | select(.not_after > now) | .not_after' | wc -l

# Use staging environment first
certbot certonly --staging --webroot -w /var/www/certbot -d yourdomain.com
```

#### 3. Domain Validation Failures

```bash
# Check DNS resolution
nslookup yourdomain.com
dig yourdomain.com A

# Test HTTP challenge access
curl http://yourdomain.com/.well-known/acme-challenge/test

# Check firewall
sudo ufw status
sudo iptables -L
```

#### 4. Mixed Content Errors

```bash
# Check HTTPS URLs in environment
grep -r "http://" .env

# Update frontend API URLs
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
```

#### 5. Certificate Chain Issues

```bash
# Check certificate chain
openssl s_client -servername yourdomain.com -connect yourdomain.com:443 -showcerts

# Verify intermediate certificates included
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/yourdomain.com.crt
```

### SSL Configuration Testing

```bash
# Test SSL configuration with online tools:
# https://www.ssllabs.com/ssltest/
# https://observatory.mozilla.org/

# Test locally with testssl.sh
docker run --rm -ti drwetter/testssl.sh yourdomain.com

# Test cipher suites
nmap --script ssl-enum-ciphers -p 443 yourdomain.com
```

### Debugging Commands

```bash
# Check nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Check certificate expiration
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Check SSL protocols and ciphers
nmap --script ssl-cert,ssl-enum-ciphers -p 443 yourdomain.com

# Monitor nginx access logs
docker-compose -f docker-compose.prod.yml logs -f nginx
```

## Security Considerations

### Production Security Checklist

- [ ] **Strong SSL Configuration**: TLS 1.2+ only, strong cipher suites
- [ ] **HSTS Headers**: HTTP Strict Transport Security enabled
- [ ] **Security Headers**: CSP, XSS protection, content type sniffing protection
- [ ] **Perfect Forward Secrecy**: ECDHE cipher suites preferred
- [ ] **Certificate Transparency**: OCSP stapling enabled
- [ ] **Regular Updates**: nginx and SSL certificates kept current
- [ ] **Monitoring**: SSL health checks and expiration monitoring
- [ ] **Rate Limiting**: API and upload endpoints protected

### Security Headers Implemented

```nginx
# Security headers in nginx configuration:
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### SSL Configuration Hardening

```nginx
# Strong SSL configuration:
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...;
ssl_prefer_server_ciphers off;
ssl_session_tickets off;
```

### Certificate Security

- **Private Key Protection**: 600 permissions, stored securely
- **Certificate Validation**: Regular validation and renewal
- **Chain of Trust**: Complete certificate chain included
- **Revocation Checking**: OCSP stapling enabled

## Advanced Configuration

### Multi-Domain Setup

```nginx
# Configure multiple domains in nginx
server {
    listen 443 ssl http2;
    server_name app.yourdomain.com api.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    
    # Configuration...
}
```

### Load Balancing with SSL

```yaml
# Docker Compose with multiple backend instances
backend:
  deploy:
    replicas: 3
  # Configuration...

nginx:
  # nginx.conf updated for load balancing
```

### SSL Termination at Load Balancer

For deployments behind AWS ALB, Cloudflare, etc.:

```nginx
# Trust proxy headers
set_real_ip_from 10.0.0.0/8;
real_ip_header X-Forwarded-For;

# Handle SSL termination at load balancer
if ($http_x_forwarded_proto != "https") {
    return 301 https://$host$request_uri;
}
```

## Support and Resources

### Documentation Links

- [nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [SSL Labs Testing](https://www.ssllabs.com/ssltest/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

### SSL Testing Tools

- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Observatory**: https://observatory.mozilla.org/
- **testssl.sh**: https://testssl.sh/
- **OpenSSL**: Command-line SSL testing

### Getting Help

1. Check nginx and certbot logs
2. Run SSL health check script
3. Verify DNS and firewall configuration
4. Test with SSL testing tools
5. Check the troubleshooting section above
