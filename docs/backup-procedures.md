# Backup and Recovery Procedures
**3D Print Management System - Masterplan Compliant Backup Strategy**

This document provides comprehensive backup and recovery procedures for the 3D Print Management System, implementing the backup strategy defined in Section 5.8 of the masterplan.

## Table of Contents

1. [Overview](#overview)
2. [Backup Strategy](#backup-strategy)
3. [Setup and Configuration](#setup-and-configuration)
4. [Daily Operations](#daily-operations)
5. [Recovery Procedures](#recovery-procedures)
6. [Verification and Testing](#verification-and-testing)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Emergency Procedures](#emergency-procedures)

---

## Overview

### Backup Components
The system backs up two critical components in synchronized fashion:
- **PostgreSQL Database**: Complete SQL dump including all job records, user data, audit logs
- **File Storage**: Complete archive of all uploaded files, job artifacts, and metadata

### Key Features
- **Synchronized Backups**: Database and file storage are backed up sequentially to minimize synchronization window
- **Multi-Tier Retention**: Daily (14 days), Weekly (2 months), Monthly (1 year)
- **Off-Site Storage**: Automated transfer to secure remote location
- **Integrity Verification**: Comprehensive validation of all backup files
- **Automated Monitoring**: Email notifications for backup success/failure
- **Safe Recovery**: Pre-restore backups and integrity audits

---

## Backup Strategy

### Automated Schedule
| Backup Type | Frequency | Retention | Storage Location |
|------------|-----------|-----------|------------------|
| Daily | Every day at 3:00 AM | 14 days | `backups/daily/` |
| Weekly | Sundays at 3:00 AM | 2 months | `backups/weekly/` |
| Monthly | 1st of month at 3:00 AM | 1 year | `backups/monthly/` |

### Backup Process Flow
1. **Database Backup**: pg_dump creates complete SQL dump
2. **Immediate File Storage Backup**: tar.gz archive of entire storage directory
3. **Verification**: Integrity checks on both backup files
4. **Organization**: Backups moved to appropriate retention tier
5. **Off-Site Sync**: Transfer to secure remote storage
6. **Monitoring**: Email notifications sent for success/failure

### Security and Storage
- All backups are compressed (gzip/tar.gz) to save space
- Off-site storage **required** for disaster protection
- Backup integrity verified before considering backup complete
- Pre-restore safety backups created before any restore operation

---

## Setup and Configuration

### Prerequisites
- Docker and Docker Compose installed
- PostgreSQL database running in container
- Sufficient disk space for backups (estimate: database size × 3 + storage size × 3)
- Email server access for notifications (optional but recommended)
- Off-site storage location configured

### Installation

1. **Ensure Scripts are Executable**:
   ```bash
   chmod +x scripts/backup_database.sh
   chmod +x scripts/restore_database.sh
   ```

2. **Create Backup Directory Structure**:
   ```bash
   mkdir -p backups/{daily,weekly,monthly,logs}
   ```

3. **Configure Environment Variables** (in `.env` file):
   ```bash
   # Backup Configuration
   BACKUP_BASE_DIR="/path/to/backups"
   STORAGE_PATH="/path/to/storage"
   DOCKER_COMPOSE_FILE="/path/to/docker-compose.prod.yml"
   DB_CONTAINER="db"
   DB_USER="postgres"
   DB_NAME="3d_print_system"
   
   # Off-Site Storage (choose one)
   OFFSITE_ENABLED="true"
   OFFSITE_TYPE="rsync"  # rsync, s3, or scp
   OFFSITE_DESTINATION="user@backup-server:/backup/3d-print-system/"
   OFFSITE_OPTIONS="-e 'ssh -i /path/to/key'"
   
   # Email Notifications
   EMAIL_ENABLED="true"
   EMAIL_TO="admin@yourdomain.com"
   EMAIL_FROM="backup@yourdomain.com"
   EMAIL_SMTP_HOST="smtp.yourdomain.com"
   EMAIL_SUBJECT_PREFIX="[3D Print Backup]"
   ```

4. **Set Up Automated Backup Schedule**:
   ```bash
   # Add to system crontab
   sudo crontab -e
   
   # Add this line for daily backups at 3:00 AM
   0 3 * * * /path/to/3d-print-system/scripts/backup_database.sh >> /var/log/3d-print-backup.log 2>&1
   ```

### Off-Site Storage Configuration

#### Option 1: rsync over SSH
```bash
OFFSITE_TYPE="rsync"
OFFSITE_DESTINATION="backup-user@backup.university.edu:/secure/backups/3d-print/"
OFFSITE_OPTIONS="-e 'ssh -i /path/to/backup-key'"
```

#### Option 2: AWS S3
```bash
OFFSITE_TYPE="s3"
OFFSITE_DESTINATION="s3://university-backups/3d-print-system/"
OFFSITE_OPTIONS="--storage-class GLACIER"
```

#### Option 3: SCP
```bash
OFFSITE_TYPE="scp"
OFFSITE_DESTINATION="backup-user@secure-server.edu:/vault/3d-print/"
OFFSITE_OPTIONS="-i /path/to/backup-key"
```

---

## Daily Operations

### Manual Backup
To create an immediate backup:
```bash
./scripts/backup_database.sh
```

### Test Configuration
Verify setup without creating backups:
```bash
./scripts/backup_database.sh --test-mode
```

### Check Backup Status
View recent backup logs:
```bash
tail -f backups/logs/backup_*.log
```

### List Available Backups
```bash
./scripts/restore_database.sh --list-backups
```

### Verify Backup Integrity
```bash
./scripts/restore_database.sh --verify-backup 20231215
```

---

## Recovery Procedures

### Emergency Recovery Steps

#### 1. Assess the Situation
- Identify the scope of data loss or corruption
- Determine the most recent viable backup date
- Ensure system downtime is acceptable

#### 2. List Available Backups
```bash
./scripts/restore_database.sh --list-backups
```

#### 3. Verify Backup Integrity
```bash
./scripts/restore_database.sh --verify-backup YYYYMMDD
```

#### 4. Perform Restore
```bash
./scripts/restore_database.sh --backup-date YYYYMMDD
```

**⚠️ WARNING**: This will overwrite all current data!

#### 5. Post-Restore Verification
- System will automatically run integrity audit
- Verify all services are running
- Test critical functionality
- Check file access and job operations

### Restore Process Details

The restore script performs these steps automatically:

1. **Pre-Restore Safety Backup**: Creates backup of current state
2. **System Shutdown**: Stops all services safely
3. **Database Restore**: Recreates database from SQL dump
4. **File Storage Restore**: Extracts files to storage directory
5. **System Startup**: Restarts all services
6. **Integrity Audit**: Runs automated system health check
7. **Verification Report**: Provides summary and next steps

### Partial Recovery Options

#### Database Only Recovery
```bash
# Extract database from backup manually
zcat backups/daily/database_daily_20231215.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T db \
psql -U postgres -d 3d_print_system
```

#### File Storage Only Recovery
```bash
# Extract files from backup manually
tar -xzf backups/daily/storage_daily_20231215.tar.gz -C /path/to/parent/
```

---

## Verification and Testing

### Quarterly Restore Testing
**Required by Masterplan**: Perform test restore every 3 months to validate procedures.

1. **Set Up Test Environment**:
   ```bash
   # Create isolated test environment
   cp docker-compose.prod.yml docker-compose.test.yml
   # Edit ports and volume names to avoid conflicts
   ```

2. **Perform Test Restore**:
   ```bash
   # Use test environment for restore
   DOCKER_COMPOSE_FILE="docker-compose.test.yml" \
   STORAGE_PATH="/tmp/test-storage" \
   ./scripts/restore_database.sh --backup-date YYYYMMDD
   ```

3. **Validate Functionality**:
   - Access test system via different port
   - Verify job data integrity
   - Test file downloads
   - Check admin functions

4. **Document Results**:
   - Record test date and backup date used
   - Note any issues or improvements needed
   - Update procedures if necessary

### Daily Verification
Automated verification includes:
- Backup file integrity (gzip/tar validity)
- File size reasonableness checks
- SQL dump header validation
- File count consistency

### Weekly Health Check
```bash
# Check backup storage usage
du -sh backups/

# Verify recent backups exist
ls -la backups/daily/ | tail -7

# Check off-site sync status
# (varies by storage type)
```

---

## Monitoring and Maintenance

### Log Monitoring
Backup logs are stored in `backups/logs/` with rotation:
- Individual backup logs: `backup_YYYYMMDD_HHMMSS.log`
- System cron log: `/var/log/3d-print-backup.log`
- Log retention: 30 days

### Email Notifications
Configure email alerts for:
- **Success**: Daily backup completion summary
- **Failure**: Immediate alert with error details
- **Warning**: Off-site sync failures or verification issues

### Storage Management
Automatic retention policy:
- **Daily backups**: Deleted after 14 days
- **Weekly backups**: Deleted after 2 months
- **Monthly backups**: Deleted after 1 year
- **Logs**: Deleted after 30 days

### Capacity Planning
Monitor storage usage and plan for growth:
```bash
# Check current usage
df -h /path/to/backups
du -sh /path/to/backups/*

# Estimate future needs
# Daily growth × retention periods × buffer
```

---

## Troubleshooting

### Common Issues and Solutions

#### Backup Script Fails to Start
**Symptoms**: Cron job fails, no backup log created

**Diagnosis**:
```bash
# Test script manually
./scripts/backup_database.sh --test-mode

# Check permissions
ls -la scripts/backup_database.sh

# Check environment
./scripts/backup_database.sh --config /path/to/.env
```

**Solutions**:
- Ensure script is executable: `chmod +x scripts/backup_database.sh`
- Verify configuration file path and contents
- Check Docker Compose file path

#### Database Backup Fails
**Symptoms**: "Database dump failed" in logs

**Diagnosis**:
```bash
# Test database connection
docker-compose -f docker-compose.prod.yml exec db \
pg_isready -U postgres -d 3d_print_system

# Test manual dump
docker-compose -f docker-compose.prod.yml exec db \
pg_dump -U postgres -d 3d_print_system > test_backup.sql
```

**Solutions**:
- Verify database container is running
- Check database credentials in configuration
- Ensure sufficient disk space

#### Storage Backup Fails
**Symptoms**: "File storage backup failed" in logs

**Diagnosis**:
```bash
# Check storage directory
ls -la /path/to/storage

# Test manual archive
tar -czf test_storage.tar.gz -C /path/to/parent storage/
```

**Solutions**:
- Verify storage directory exists and is readable
- Check available disk space
- Ensure no files are locked or in use

#### Off-Site Sync Fails
**Symptoms**: Local backups succeed but off-site sync fails

**Diagnosis**:
```bash
# Test connection manually
rsync --dry-run -avz backups/ user@server:/path/
ssh user@server "ls -la /path/"
```

**Solutions**:
- Verify SSH keys and permissions
- Check network connectivity
- Validate off-site destination path
- Review firewall and security group settings

#### Restore Process Fails
**Symptoms**: Restore script exits with error

**Common Solutions**:
1. **Backup integrity issues**: Re-verify backup files
2. **Insufficient disk space**: Clear space or use different volume
3. **Database connection issues**: Ensure database container starts properly
4. **Permission issues**: Check file ownership and permissions

### Recovery from Failed Restore
If restore process fails partway through:

1. **Check pre-restore backup**:
   ```bash
   ls -la backups/temp/restore_*/pre_restore_backup/
   ```

2. **Restart system services**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Restore from pre-restore backup if needed**:
   ```bash
   # Manual recovery using pre-restore backup
   # (Contact system administrator)
   ```

---

## Emergency Procedures

### Complete System Failure
If both primary system and local backups are unavailable:

1. **Assess Available Backups**:
   - Check off-site storage for latest backups
   - Verify integrity of off-site backup files

2. **Prepare New System**:
   - Deploy fresh system instance
   - Configure environment variables
   - Ensure Docker and all dependencies installed

3. **Restore from Off-Site**:
   ```bash
   # Download backups from off-site storage
   rsync -avz user@backup-server:/backup/3d-print-system/ ./backups/
   
   # Proceed with normal restore process
   ./scripts/restore_database.sh --backup-date YYYYMMDD
   ```

### Data Corruption Detection
If corruption is detected during operation:

1. **Stop System Immediately**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Assess Corruption Scope**:
   - Check database integrity
   - Verify file system consistency
   - Review recent change logs

3. **Choose Recovery Strategy**:
   - **Limited corruption**: Partial restore of affected components
   - **Extensive corruption**: Complete system restore
   - **Uncertain scope**: Complete restore from known good backup

### Contact Information
In case of emergencies requiring assistance:
- **System Administrator**: [Contact Information]
- **Database Administrator**: [Contact Information]
- **IT Support Escalation**: [Contact Information]

---

## Appendix: Configuration Reference

### Complete Environment Variable List
```bash
# Required Configuration
BACKUP_BASE_DIR="/path/to/backups"
STORAGE_PATH="/path/to/storage"
DOCKER_COMPOSE_FILE="/path/to/docker-compose.prod.yml"
DB_CONTAINER="db"
DB_USER="postgres"
DB_NAME="3d_print_system"

# Off-Site Storage Configuration
OFFSITE_ENABLED="true"
OFFSITE_TYPE="rsync"        # rsync, s3, scp
OFFSITE_DESTINATION="user@server:/path/"
OFFSITE_OPTIONS=""          # Additional options for sync command

# Email Notification Configuration
EMAIL_ENABLED="true"
EMAIL_TO="admin@domain.com"
EMAIL_FROM="backup@domain.com"
EMAIL_SMTP_HOST="localhost"
EMAIL_SUBJECT_PREFIX="[3D Print Backup]"

# Advanced Options (Optional)
DAILY_RETENTION_DAYS=14
WEEKLY_RETENTION_MONTHS=2
MONTHLY_RETENTION_YEARS=1
```

### Script Command Reference

#### Backup Script Commands
```bash
# Standard operations
./scripts/backup_database.sh                    # Run full backup
./scripts/backup_database.sh --test-mode        # Test configuration
./scripts/backup_database.sh --config /path     # Use custom config

# Advanced options
BACKUP_BASE_DIR=/custom/path ./scripts/backup_database.sh
EMAIL_ENABLED=false ./scripts/backup_database.sh
```

#### Restore Script Commands
```bash
# Information commands
./scripts/restore_database.sh --list-backups           # List available backups
./scripts/restore_database.sh --verify-backup DATE     # Verify specific backup
./scripts/restore_database.sh --help                   # Show help

# Restore operations
./scripts/restore_database.sh --backup-date YYYYMMDD   # Interactive restore
./scripts/restore_database.sh --backup-date YYYYMMDD --yes  # Skip confirmations
./scripts/restore_database.sh --dry-run --backup-date YYYYMMDD  # Preview only

# Advanced restore options
./scripts/restore_database.sh --backup-date YYYYMMDD --config /path
./scripts/restore_database.sh --backup-date YYYYMMDD --force
```

### Cron Job Examples
```bash
# Daily backup at 3:00 AM with logging
0 3 * * * /path/to/scripts/backup_database.sh >> /var/log/3d-print-backup.log 2>&1

# Weekly verification on Saturdays at 2:00 AM
0 2 * * 6 /path/to/scripts/restore_database.sh --verify-backup $(date -d '1 day ago' +\%Y\%m\%d) >> /var/log/backup-verify.log 2>&1

# Monthly cleanup on 1st of month at 1:00 AM
0 1 1 * * find /path/to/backups/logs -name "*.log" -mtime +30 -delete
```

---

## Document Information

**Document Version**: 1.0.0  
**Last Updated**: Current Implementation  
**Masterplan Compliance**: Section 5.8 - Backup and Disaster Recovery  
**Review Schedule**: Quarterly (with restore testing)  
**Next Review Due**: [Date + 3 months]  

**Maintained By**: System Administrator  
**Approved By**: IT Manager  

---

*This document is part of the 3D Print Management System documentation suite. For system architecture and operational procedures, see the main documentation directory.*
