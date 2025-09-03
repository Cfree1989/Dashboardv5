# Environment Setup Guide

This document provides comprehensive information about all environment variables used in the 3D Print Management System and how to configure them for different environments.

## Quick Start

1. Copy `env.example` to `.env` in the project root
2. Update the values according to your environment
3. Follow the configuration sections below for detailed guidance

```bash
cp env.example .env
# Edit .env with your specific values
```

## Environment Variables Reference

### Core Application Settings

#### `FLASK_APP` (Required)
- **Description**: Entry point for the Flask application
- **Default**: `run.py`
- **Values**: `run.py` (do not change)

#### `FLASK_ENV` (Required)
- **Description**: Flask environment mode
- **Default**: `development`
- **Values**: 
  - `development` - For local development with debug features
  - `production` - For production deployment with optimizations
- **Security**: Always use `production` in live environments

#### `SECRET_KEY` (Required)
- **Description**: Secret key for Flask session security and JWT signing
- **Default**: None (must be set)
- **Format**: Random string (min 32 characters recommended)
- **Generate**: `python -c "import secrets; print(secrets.token_hex(32))"`
- **Security**: 
  - Must be unique per deployment
  - Never expose in logs or code
  - Change if compromised

#### `APP_VERSION` (Optional)
- **Description**: Application version displayed in admin interface
- **Default**: `v3.1.2`
- **Format**: Semantic version string (e.g., `v3.1.2`)

#### `ENVIRONMENT_BANNER` (Optional)
- **Description**: Banner text displayed in admin interface to identify environment
- **Default**: Empty string
- **Examples**: 
  - `Development Environment`
  - `Staging Environment`
  - `Production Environment`

### Database Configuration

#### `DATABASE_URL` (Required)
- **Description**: PostgreSQL database connection string
- **Format**: `postgresql://username:password@host:port/database_name`
- **Examples**:
  - Development: `postgresql://postgres:devpass@localhost:5432/3d_print_system`
  - Production: `postgresql://app_user:secure_pass@db.internal:5432/3d_print_system`
- **Security**: Use strong passwords and limit database access

#### `POSTGRES_USER` (Required for Docker)
- **Description**: PostgreSQL username (used by docker-compose)
- **Default**: `postgres`
- **Recommendation**: Use a dedicated application user in production

#### `POSTGRES_PASSWORD` (Required for Docker)
- **Description**: PostgreSQL password (used by docker-compose)
- **Security**: Use strong, unique passwords (min 16 characters)

#### `POSTGRES_DB` (Required for Docker)
- **Description**: PostgreSQL database name
- **Default**: `3d_print_system`

### Redis Configuration

#### `REDIS_URL` (Required)
- **Description**: Redis connection URL for caching and queues
- **Format**: `redis://[:password@]host:port[/database]`
- **Examples**:
  - With password: `redis://:mypassword@redis:6379`
  - Without password: `redis://redis:6379`

#### `REDIS_PASSWORD` (Recommended)
- **Description**: Redis authentication password
- **Security**: Use strong passwords for production
- **Note**: Redis should not be exposed to public internet

#### `ANALYTICS_CACHE_TTL` (Optional)
- **Description**: Time-to-live for analytics cache in seconds
- **Default**: `60`
- **Range**: 30-3600 (30 seconds to 1 hour)

### Email Configuration

#### `MAIL_SERVER` (Required for email features)
- **Description**: SMTP server hostname
- **Examples**:
  - Office 365: `smtp.office365.com`
  - Gmail: `smtp.gmail.com`
  - Custom: `mail.yourdomain.com`

#### `MAIL_PORT` (Required for email features)
- **Description**: SMTP server port
- **Default**: `587`
- **Common values**:
  - `587` - STARTTLS (recommended)
  - `465` - SSL/TLS
  - `25` - Plain (not recommended)

#### `MAIL_USE_TLS` (Required for email features)
- **Description**: Enable TLS encryption for email
- **Default**: `true`
- **Values**: `true` or `false`
- **Security**: Always use `true` for production

#### `MAIL_USERNAME` (Required for email features)
- **Description**: SMTP authentication username
- **Format**: Usually an email address
- **Example**: `no-reply@yourdomain.com`

#### `MAIL_PASSWORD` (Required for email features)
- **Description**: SMTP authentication password or app password
- **Security**: Use app passwords for Gmail/Office 365
- **Storage**: Never commit to source control

#### `MAIL_DEFAULT_SENDER` (Required for email features)
- **Description**: Default sender for outgoing emails
- **Format**: `Name <email@domain.com>`
- **Example**: `3D Print System <no-reply@yourdomain.com>`

### JWT Authentication

#### `JWT_COOKIE_NAME` (Optional)
- **Description**: Name of the authentication cookie
- **Default**: `auth_token`

#### `JWT_COOKIE_SECURE` (Critical for production)
- **Description**: Require HTTPS for JWT cookies
- **Default**: `false`
- **Values**: `true` or `false`
- **Security**: Must be `true` in production with HTTPS

#### `JWT_COOKIE_HTTPONLY` (Recommended)
- **Description**: Prevent JavaScript access to JWT cookies
- **Default**: `true`
- **Security**: Keep as `true` to prevent XSS attacks

#### `JWT_COOKIE_SAMESITE` (Security)
- **Description**: SameSite cookie attribute
- **Default**: `Lax`
- **Values**: `Strict`, `Lax`, `None`

#### `JWT_COOKIE_DOMAIN` (Production)
- **Description**: Cookie domain restriction
- **Default**: Empty (current domain)
- **Example**: `yourdomain.com`
- **Note**: Set for production to restrict cookie scope

#### `JWT_COOKIE_PATH` (Optional)
- **Description**: Cookie path restriction
- **Default**: `/`

#### `JWT_COOKIE_MAX_AGE` (Optional)
- **Description**: JWT cookie expiration in seconds
- **Default**: `43200` (12 hours)
- **Range**: 3600-86400 (1-24 hours)

### Workstation Authentication

#### `WORKSTATION_DEVELOPMENT` (Development only)
- **Description**: Password for development workstation access
- **Default**: `password123`
- **Security**: Change default value

#### `WORKSTATION_1`, `WORKSTATION_2`, `WORKSTATION_3` (Required)
- **Description**: Passwords for production workstation access
- **Default**: `Fabrication`, `Engineering`, `AdminWorkstation`
- **Security**: Use strong, unique passwords for each workstation

### File Handling Configuration

#### `STORAGE_PATH` (Required)
- **Description**: Base directory for file storage
- **Default**: `storage`
- **Format**: Relative or absolute path
- **Examples**:
  - Development: `storage`
  - Production: `/app/storage` or `/data/storage`

#### `ALLOWED_FILE_EXTENSIONS` (Optional)
- **Description**: Comma-separated list of allowed file extensions
- **Default**: `stl,obj,3mf,form,idea`
- **Format**: Extensions without dots, comma-separated
- **Example**: `stl,obj,3mf,ply,step`

#### `FILE_EXTENSION_PRIORITY` (Optional)
- **Description**: Priority order for file type selection
- **Default**: `3mf,form,idea,stl,obj`
- **Format**: Extensions in priority order, comma-separated

#### `MAX_FILE_SIZE_MB` (Optional)
- **Description**: Maximum file upload size in megabytes
- **Default**: `50`
- **Range**: 1-1000 (adjust based on storage capacity)

#### `MIN_FILE_SIZE_KB` (Optional)
- **Description**: Minimum file size in kilobytes to prevent empty uploads
- **Default**: `1`
- **Range**: 1-1000

#### `ATOMIC_FILE_OPERATIONS_ENABLED` (Optional)
- **Description**: Enable atomic file operations with integrity checks
- **Default**: `true`
- **Values**: `true` or `false`
- **Recommendation**: Keep `true` for data integrity

### Frontend Integration

#### `FRONTEND_PUBLIC_URL` (Required)
- **Description**: Public URL for the frontend application (used in emails)
- **Examples**:
  - Development: `http://localhost:3000`
  - Production: `https://print.yourdomain.com`
- **Security**: Use HTTPS in production

#### `NEXT_PUBLIC_API_URL` (Required)
- **Description**: API URL accessible from browser (Next.js public variable)
- **Examples**:
  - Development: `http://localhost:5000/api/v1`
  - Production: `https://api.yourdomain.com/api/v1`

#### `NODE_ENV` (Required for frontend)
- **Description**: Node.js environment mode
- **Values**:
  - `development` - Development mode with debug features
  - `production` - Production mode with optimizations

## Environment-Specific Configuration

### Development Environment

```bash
# Core settings
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-secret-key-change-me

# Local database
DATABASE_URL=postgresql://postgres:devpass@localhost:5432/3d_print_system

# Local services
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=devpass

# Frontend
FRONTEND_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:5000/api/v1
NODE_ENV=development

# Email (optional for dev)
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=true
# MAIL_USERNAME and MAIL_PASSWORD can be omitted for dev
```

### Production Environment

```bash
# Core settings
FLASK_ENV=production
SECRET_KEY=<generated-strong-secret-key>
ENVIRONMENT_BANNER=Production Environment

# Secure database
DATABASE_URL=postgresql://app_user:secure_password@db.internal:5432/3d_print_system

# Secure Redis
REDIS_URL=redis://:secure_redis_password@redis.internal:6379
REDIS_PASSWORD=secure_redis_password

# HTTPS URLs
FRONTEND_PUBLIC_URL=https://print.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NODE_ENV=production

# Secure JWT
JWT_COOKIE_SECURE=true
JWT_COOKIE_DOMAIN=yourdomain.com

# Email configuration (required)
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=no-reply@yourdomain.com
MAIL_PASSWORD=<app-password>
MAIL_DEFAULT_SENDER=3D Print System <no-reply@yourdomain.com>

# Strong workstation passwords
WORKSTATION_1=<strong-password-1>
WORKSTATION_2=<strong-password-2>
WORKSTATION_3=<strong-password-3>
```

## Security Best Practices

### General Security
1. Never commit `.env` files to version control
2. Use strong, unique passwords (minimum 16 characters)
3. Rotate secrets regularly
4. Limit access to environment configuration files
5. Use different secrets for each environment

### Production Security
1. Enable HTTPS for all services
2. Set `JWT_COOKIE_SECURE=true`
3. Use dedicated service accounts for external services
4. Restrict database and Redis access to internal network
5. Monitor for unauthorized access attempts

### Secret Generation
```bash
# Generate a strong SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a strong password
python -c "import secrets; print(secrets.token_urlsafe(20))"

# Generate multiple secrets at once
python -c "
import secrets
print('SECRET_KEY=' + secrets.token_hex(32))
print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(20))
print('REDIS_PASSWORD=' + secrets.token_urlsafe(20))
print('WORKSTATION_1=' + secrets.token_urlsafe(16))
print('WORKSTATION_2=' + secrets.token_urlsafe(16))
print('WORKSTATION_3=' + secrets.token_urlsafe(16))
"
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
- Check `DATABASE_URL` format
- Verify database server is running
- Confirm network connectivity
- Check user permissions

#### Redis Connection Issues
- Verify Redis server is running
- Check `REDIS_URL` format
- Confirm password if authentication is enabled
- Test network connectivity

#### Email Not Working
- Verify SMTP server settings
- Check authentication credentials
- Confirm firewall allows SMTP traffic
- Test with email client using same settings

#### File Upload Issues
- Check `STORAGE_PATH` permissions
- Verify disk space availability
- Confirm `MAX_FILE_SIZE_MB` setting
- Check `ALLOWED_FILE_EXTENSIONS` list

#### JWT Authentication Issues
- Verify `SECRET_KEY` is set and consistent
- Check `JWT_COOKIE_SECURE` matches HTTPS usage
- Confirm cookie domain settings
- Check browser console for cookie errors

### Validation Commands

```bash
# Test database connection
python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    conn = engine.connect()
    print('Database connection: OK')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Test Redis connection
python -c "
import os, redis
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('Redis connection: OK')
except Exception as e:
    print(f'Redis connection failed: {e}')
"

# Test email configuration (requires Flask app context)
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from flask_mail import Mail
    mail = Mail(app)
    print('Email configuration: OK')
"
```

## Environment Variables Checklist

### Development Setup
- [ ] `SECRET_KEY` set to a development value
- [ ] `DATABASE_URL` points to development database
- [ ] `REDIS_URL` points to development Redis
- [ ] `FRONTEND_PUBLIC_URL` set to `http://localhost:3000`
- [ ] `STORAGE_PATH` directory exists and is writable

### Production Setup
- [ ] `FLASK_ENV=production`
- [ ] `SECRET_KEY` is a strong, randomly generated value
- [ ] `DATABASE_URL` uses secure credentials
- [ ] `REDIS_PASSWORD` is set with strong password
- [ ] `JWT_COOKIE_SECURE=true`
- [ ] `FRONTEND_PUBLIC_URL` uses HTTPS
- [ ] `MAIL_*` settings configured for email notifications
- [ ] `WORKSTATION_*` passwords are strong and unique
- [ ] `ENVIRONMENT_BANNER` clearly indicates production

## Support

For additional help with environment configuration:

1. Check the [Deployment Guide](deployment-guide.md)
2. Review application logs for specific error messages
3. Use the validation commands above to test individual components
4. Consult the [Troubleshooting Section](deployment-guide.md#troubleshooting) in the deployment guide
