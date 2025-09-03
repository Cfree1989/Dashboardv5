# 3D Print Management System - Deployment Guide

This guide provides step-by-step instructions for deploying the 3D Print Management System in both development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Database Setup](#database-setup)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Health Verification](#health-verification)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB free space
- **Network**: Internet access for package downloads

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 100GB+ SSD
- **Network**: Reliable internet connection with static IP (production)

### Required Software

#### Docker Deployment (Recommended)
- Docker Engine 20.10+ 
- Docker Compose 2.0+
- Git

#### Manual Deployment (Advanced)
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- nginx (production)

### Installation Commands

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Install Git
sudo apt install git -y

# Logout and login to apply docker group changes
```

#### CentOS/RHEL/Fedora
```bash
# Update system
sudo dnf update -y

# Install Docker
sudo dnf install docker docker-compose-plugin -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Git
sudo dnf install git -y
```

## Development Deployment

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd Dashboardv5

# Verify directory structure
ls -la
```

### Step 2: Environment Configuration

```bash
# Create environment file from example
cp env.example .env

# Edit environment variables (use your preferred editor)
nano .env
```

**Required Development Settings:**
```bash
# Core settings
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-me

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=devpass123
DATABASE_URL=postgresql://postgres:devpass123@db:5432/3d_print_system

# Redis
REDIS_PASSWORD=devredispass
REDIS_URL=redis://:devredispass@redis:6379

# Frontend
FRONTEND_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1

# Workstation passwords (change these)
WORKSTATION_DEVELOPMENT=password123
WORKSTATION_1=DevFab123
WORKSTATION_2=DevEng123
WORKSTATION_3=DevAdmin123
```

### Step 3: Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs to monitor startup
docker-compose -f docker-compose.dev.yml logs -f

# Wait for services to be healthy (2-3 minutes)
docker-compose -f docker-compose.dev.yml ps
```

### Step 4: Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.dev.yml exec backend python -m flask db upgrade

# (Optional) Seed with test data
docker-compose -f docker-compose.dev.yml exec backend python -c "
from app import create_app, db
from app.seed import create_test_data
app = create_app()
with app.app_context():
    create_test_data()
"
```

### Step 5: Verify Development Setup

```bash
# Check service health
curl http://localhost:5000/health
curl http://localhost:3000

# Access the application
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000/api/v1"
```

## Production Deployment

### Step 1: Server Preparation

```bash
# Create application user
sudo useradd -m -s /bin/bash appuser
sudo usermod -aG docker appuser

# Create application directory
sudo mkdir -p /opt/3d-print-system
sudo chown appuser:appuser /opt/3d-print-system

# Switch to application user
sudo su - appuser
cd /opt/3d-print-system
```

### Step 2: Security Hardening

```bash
# Set up firewall (adjust ports as needed)
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
# Note: Don't expose database/redis ports (5432, 6379) to internet

# Configure fail2ban (optional but recommended)
sudo apt install fail2ban -y
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone <repository-url> .
git checkout main  # Or your production branch

# Create production environment file
cp env.example .env
```

### Step 4: Production Environment Configuration

```bash
# Edit production environment (use secure values!)
nano .env
```

**Critical Production Settings:**
```bash
# Core settings
FLASK_ENV=production
SECRET_KEY=<generate-strong-secret-key>
ENVIRONMENT_BANNER=Production Environment

# Database with strong password
POSTGRES_USER=printapp
POSTGRES_PASSWORD=<strong-database-password>
DATABASE_URL=postgresql://printapp:<strong-database-password>@db:5432/3d_print_system

# Redis with authentication
REDIS_PASSWORD=<strong-redis-password>
REDIS_URL=redis://:<strong-redis-password>@redis:6379

# HTTPS URLs (adjust your domain)
FRONTEND_PUBLIC_URL=https://print.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1

# Secure JWT settings
JWT_COOKIE_SECURE=true
JWT_COOKIE_DOMAIN=yourdomain.com

# Email configuration (required for production)
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=no-reply@yourdomain.com
MAIL_PASSWORD=<app-password>
MAIL_DEFAULT_SENDER=3D Print System <no-reply@yourdomain.com>

# Strong workstation passwords
WORKSTATION_1=<strong-workstation-password-1>
WORKSTATION_2=<strong-workstation-password-2>
WORKSTATION_3=<strong-workstation-password-3>
```

**Generate Secure Secrets:**
```bash
# Generate strong secrets
python3 -c "
import secrets
print('SECRET_KEY=' + secrets.token_hex(32))
print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(20))
print('REDIS_PASSWORD=' + secrets.token_urlsafe(20))
print('WORKSTATION_1=' + secrets.token_urlsafe(16))
print('WORKSTATION_2=' + secrets.token_urlsafe(16))
print('WORKSTATION_3=' + secrets.token_urlsafe(16))
"
```

### Step 5: Production Deployment

```bash
# Create storage directory
mkdir -p storage/{Uploaded,Pending,ReadyToPrint,Printing,Completed,PaidPickedUp,Rejected,Archived}
chmod 755 storage
chmod 755 storage/*

# Build and start production services
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Monitor startup logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 6: Initialize Production Database

```bash
# Wait for database to be ready
sleep 30

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python -m flask db upgrade

# Create initial staff account (optional)
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app import create_app, db
from app.models.staff import Staff
app = create_app()
with app.app_context():
    admin = Staff(username='admin', email='admin@yourdomain.com')
    admin.set_password('change-this-password')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created')
"
```

## Database Setup

### PostgreSQL Configuration

#### Development Database
The development setup uses Docker containers with default PostgreSQL configuration.

#### Production Database Hardening

```bash
# Connect to PostgreSQL container
docker-compose -f docker-compose.prod.yml exec db psql -U postgres -d 3d_print_system

-- Create dedicated application user
CREATE USER printapp WITH ENCRYPTED PASSWORD '<strong-password>';
GRANT CONNECT ON DATABASE 3d_print_system TO printapp;
GRANT USAGE ON SCHEMA public TO printapp;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO printapp;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO printapp;

-- Update database URL in .env to use new user
-- DATABASE_URL=postgresql://printapp:<strong-password>@db:5432/3d_print_system
```

### Database Backup Setup

```bash
# Create backup script
cat << 'EOF' > /opt/3d-print-system/scripts/backup_db.sh
#!/bin/bash
BACKUP_DIR="/opt/3d-print-system/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/3d_print_system_backup_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

docker-compose -f /opt/3d-print-system/docker-compose.prod.yml exec -T db pg_dump -U printapp 3d_print_system > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $BACKUP_FILE.gz"
EOF

chmod +x /opt/3d-print-system/scripts/backup_db.sh

# Set up daily backup cron job
echo "0 2 * * * /opt/3d-print-system/scripts/backup_db.sh >> /var/log/db_backup.log 2>&1" | crontab -
```

## SSL/TLS Configuration

**Note**: The system now includes comprehensive SSL/TLS support with nginx reverse proxy. See the dedicated [SSL Setup Guide](ssl-setup.md) for detailed configuration instructions.

### Quick SSL Setup

#### Install nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
```

#### Configure nginx

```bash
# Create nginx configuration
sudo tee /etc/nginx/sites-available/3d-print-system << 'EOF'
server {
    listen 80;
    server_name print.yourdomain.com api.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name print.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    
    # SSL configuration (same as above)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security headers (same as above)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Handle large file uploads
        client_max_body_size 100M;
        proxy_request_buffering off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/3d-print-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate with Let's Encrypt

The system includes automated Let's Encrypt integration:

```bash
# Configure SSL in .env
DOMAIN_NAME=yourdomain.com
SSL_TYPE=letsencrypt
SSL_EMAIL=admin@yourdomain.com

# Start with SSL profile
docker-compose -f docker-compose.prod.yml --profile ssl up -d

# Monitor certificate generation
docker-compose -f docker-compose.prod.yml logs certbot

# Check SSL health
./docker/nginx/scripts/ssl-health-check.sh check
```

For detailed SSL configuration, see [SSL Setup Guide](ssl-setup.md).

## Health Verification

### Automated Health Checks

```bash
# Create health check script
cat << 'EOF' > /opt/3d-print-system/scripts/health_check.sh
#!/bin/bash

echo "=== 3D Print System Health Check ==="
echo "Timestamp: $(date)"

# Check Docker services
echo -e "\n--- Docker Services Status ---"
docker-compose -f /opt/3d-print-system/docker-compose.prod.yml ps

# Check application health endpoints
echo -e "\n--- Application Health ---"
curl -s http://localhost:5000/health | python3 -m json.tool
curl -s http://localhost:5000/api/v1/monitoring/health | python3 -m json.tool

# Check frontend
echo -e "\n--- Frontend Status ---"
if curl -s http://localhost:3000 > /dev/null; then
    echo "Frontend: OK"
else
    echo "Frontend: ERROR"
fi

# Check database connectivity
echo -e "\n--- Database Connectivity ---"
if docker-compose -f /opt/3d-print-system/docker-compose.prod.yml exec -T db pg_isready -U printapp > /dev/null; then
    echo "Database: OK"
else
    echo "Database: ERROR"
fi

# Check Redis
echo -e "\n--- Redis Status ---"
if docker-compose -f /opt/3d-print-system/docker-compose.prod.yml exec -T redis redis-cli --no-auth-warning -a $REDIS_PASSWORD ping > /dev/null; then
    echo "Redis: OK"
else
    echo "Redis: ERROR"
fi

# Check storage directory
echo -e "\n--- Storage Status ---"
if [ -w "/opt/3d-print-system/storage" ]; then
    echo "Storage: OK (writable)"
    echo "Storage usage: $(du -sh /opt/3d-print-system/storage)"
else
    echo "Storage: ERROR (not writable)"
fi

echo -e "\n=== Health Check Complete ==="
EOF

chmod +x /opt/3d-print-system/scripts/health_check.sh

# Run initial health check
./scripts/health_check.sh
```

### Monitoring Setup

```bash
# Create monitoring script
cat << 'EOF' > /opt/3d-print-system/scripts/monitor_system.sh
#!/bin/bash

LOG_FILE="/var/log/3d-print-system.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Check if services are running
check_services() {
    local services=("backend" "frontend" "db" "redis" "worker")
    for service in "${services[@]}"; do
        if ! docker-compose -f /opt/3d-print-system/docker-compose.prod.yml ps $service | grep -q "Up"; then
            log_message "ALERT: Service $service is not running"
            # Restart service
            docker-compose -f /opt/3d-print-system/docker-compose.prod.yml restart $service
            log_message "INFO: Attempted to restart service $service"
        fi
    done
}

# Check disk space
check_disk_space() {
    local usage=$(df /opt/3d-print-system | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 80 ]; then
        log_message "ALERT: Disk usage is $usage%"
    fi
}

# Main monitoring loop
check_services
check_disk_space

log_message "INFO: System monitoring check completed"
EOF

chmod +x /opt/3d-print-system/scripts/monitor_system.sh

# Set up monitoring cron job (every 5 minutes)
echo "*/5 * * * * /opt/3d-print-system/scripts/monitor_system.sh" | crontab -
```

## Maintenance

### Regular Maintenance Tasks

#### Daily Tasks (Automated)
- Database backup
- Log rotation
- Health monitoring

#### Weekly Tasks
- Update Docker images (if updates available)
- Review system logs
- Check storage usage
- Verify backup integrity

#### Monthly Tasks
- Security updates
- Certificate renewal verification
- Performance review
- Capacity planning

### Update Procedure

```bash
# Create update script
cat << 'EOF' > /opt/3d-print-system/scripts/update_system.sh
#!/bin/bash

cd /opt/3d-print-system

echo "Starting system update..."

# Backup database
./scripts/backup_db.sh

# Pull latest changes
git fetch origin
git checkout main
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
sleep 30
docker-compose -f docker-compose.prod.yml exec backend python -m flask db upgrade

# Health check
./scripts/health_check.sh

echo "System update completed"
EOF

chmod +x /opt/3d-print-system/scripts/update_system.sh
```

### Log Management

```bash
# Configure log rotation
sudo tee /etc/logrotate.d/3d-print-system << 'EOF'
/var/log/3d-print-system.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Rotate Docker logs
sudo tee -a /etc/docker/daemon.json << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
EOF

sudo systemctl restart docker
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs db

# Check resource usage
docker stats

# Restart problematic service
docker-compose -f docker-compose.prod.yml restart <service-name>
```

#### Database Connection Issues

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec db psql -U printapp -d 3d_print_system -c "SELECT version();"

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE

# Reset database connection
docker-compose -f docker-compose.prod.yml restart backend
```

#### Email Not Working

```bash
# Test email settings from backend
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app import create_app
from flask_mail import Mail, Message
app = create_app()
with app.app_context():
    mail = Mail(app)
    msg = Message('Test', recipients=['test@example.com'])
    msg.body = 'Test email'
    try:
        mail.send(msg)
        print('Email sent successfully')
    except Exception as e:
        print(f'Email error: {e}')
"
```

#### File Upload Issues

```bash
# Check storage permissions
ls -la /opt/3d-print-system/storage/
docker-compose -f docker-compose.prod.yml exec backend ls -la /app/storage/

# Fix permissions if needed
sudo chown -R 1000:1000 /opt/3d-print-system/storage/
chmod -R 755 /opt/3d-print-system/storage/
```

#### High Memory Usage

```bash
# Check container resource usage
docker stats --no-stream

# Restart services to free memory
docker-compose -f docker-compose.prod.yml restart

# Check for memory leaks in logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i memory
```

### Performance Optimization

#### Database Performance

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U printapp -d 3d_print_system

-- Check database size
SELECT pg_size_pretty(pg_database_size('3d_print_system'));

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum and analyze (run during maintenance window)
VACUUM ANALYZE;
```

#### Storage Cleanup

```bash
# Find large files
find /opt/3d-print-system/storage -type f -size +10M -ls

# Clean old archived files (older than 1 year)
find /opt/3d-print-system/storage/Archived -type f -mtime +365 -delete

# Clean Docker system
docker system prune -a --volumes
```

## Security Considerations

### Production Security Checklist

- [ ] Strong, unique passwords for all accounts
- [ ] HTTPS enabled with valid SSL certificates
- [ ] Firewall configured to block unnecessary ports
- [ ] Database and Redis not exposed to internet
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Access logging enabled
- [ ] Failed login attempt monitoring
- [ ] Environment variables secured
- [ ] Docker daemon secured

### Security Monitoring

```bash
# Monitor failed login attempts
grep "Failed login" /var/log/auth.log

# Monitor Docker daemon access
sudo journalctl -u docker.service | grep -i error

# Check for suspicious file access
sudo find /opt/3d-print-system -name "*.log" -exec grep -l "ERROR\|CRITICAL" {} \;
```

### Incident Response

1. **Immediate Response**
   - Isolate affected systems
   - Preserve logs and evidence
   - Assess scope of incident

2. **Investigation**
   - Review access logs
   - Check for unauthorized changes
   - Identify attack vectors

3. **Recovery**
   - Restore from clean backups
   - Apply security patches
   - Reset compromised credentials

4. **Post-Incident**
   - Update security measures
   - Document lessons learned
   - Review and test incident response plan

## Support and Documentation

### Additional Resources

- [Environment Setup Guide](environment-setup.md)
- [Service Interface Mapping](../backend/docs/service_interface_mapping.md)
- [Debugging Protocol](../backend/docs/debugging_protocol.md)

### Getting Help

1. Check application logs for error details
2. Use health check scripts to identify issues  
3. Review this troubleshooting section
4. Consult the environment setup guide for configuration issues

### Logging Locations

- **Application logs**: `docker-compose logs <service-name>`
- **System logs**: `/var/log/3d-print-system.log`
- **nginx logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **Database logs**: `docker-compose logs db`
