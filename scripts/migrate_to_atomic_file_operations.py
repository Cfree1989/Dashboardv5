#!/usr/bin/env python3
"""
Migration script for transitioning to atomic file operations.

This script helps migrate existing files to the new atomic file operation patterns
and provides utilities for monitoring and rollback if needed.

Usage:
    python scripts/migrate_to_atomic_file_operations.py --check
    python scripts/migrate_to_atomic_file_operations.py --migrate
    python scripts/migrate_to_atomic_file_operations.py --rollback
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app import create_app
from app.models.job import Job
from app.services.atomic_file_service import get_atomic_file_service, STATUS_TO_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtomicFileMigration:
    """Migration utility for atomic file operations."""
    
    def __init__(self):
        self.app = create_app()
        self.atomic_service = get_atomic_file_service()
        self.migration_log = []
        
    def check_file_integrity(self) -> Dict[str, List[str]]:
        """Check integrity of existing files and database records."""
        issues = {
            'orphaned_files': [],
            'missing_files': [],
            'inconsistent_paths': [],
            'metadata_sync_issues': []
        }
        
        with self.app.app_context():
            jobs = Job.query.all()
            
            for job in jobs:
                # Check if file exists
                if hasattr(job, 'file_path') and job.file_path:
                    file_path = Path(job.file_path)
                    if not file_path.exists():
                        issues['missing_files'].append(f"Job {job.id}: {job.file_path}")
                    else:
                        # Check if file is in correct status directory
                        expected_dir = self._get_expected_directory(job)
                        if file_path.parent.name != expected_dir:
                            issues['inconsistent_paths'].append(
                                f"Job {job.id}: Expected {expected_dir}, found {file_path.parent.name}"
                            )
                
                # Check metadata file
                if hasattr(job, 'metadata_path') and job.metadata_path:
                    meta_path = Path(job.metadata_path)
                    if not meta_path.exists():
                        issues['missing_files'].append(f"Job {job.id} metadata: {job.metadata_path}")
                    else:
                        # Check metadata sync
                        try:
                            with open(meta_path, 'r') as f:
                                metadata = json.load(f)
                            if metadata.get('status') != job.status:
                                issues['metadata_sync_issues'].append(
                                    f"Job {job.id}: DB status {job.status}, metadata status {metadata.get('status')}"
                                )
                        except Exception as e:
                            issues['metadata_sync_issues'].append(f"Job {job.id}: Invalid metadata - {e}")
            
            # Check for orphaned files
            storage_path = Path(os.environ.get('STORAGE_PATH', 'storage'))
            if storage_path.exists():
                for status_dir in STATUS_TO_DIR.values():
                    status_path = storage_path / status_dir
                    if status_path.exists():
                        for file_path in status_path.rglob('*'):
                            if file_path.is_file() and file_path.suffix in ['.stl', '.obj', '.gcode', '.json']:
                                # Check if this file is referenced by any job
                                found = False
                                for job in jobs:
                                    if (hasattr(job, 'file_path') and str(file_path) == job.file_path) or \
                                       (hasattr(job, 'metadata_path') and str(file_path) == job.metadata_path):
                                        found = True
                                        break
                                if not found:
                                    issues['orphaned_files'].append(str(file_path))
        
        return issues
    
    def migrate_job_files(self, job_id: Optional[int] = None, dry_run: bool = True) -> Dict[str, int]:
        """Migrate job files to atomic operation patterns."""
        results = {
            'migrated': 0,
            'failed': 0,
            'skipped': 0
        }
        
        with self.app.app_context():
            if job_id:
                jobs = [Job.query.get(job_id)]
                if not jobs[0]:
                    logger.error(f"Job {job_id} not found")
                    return results
            else:
                jobs = Job.query.all()
            
            for job in jobs:
                try:
                    if self._migrate_single_job(job, dry_run):
                        results['migrated'] += 1
                        self.migration_log.append({
                            'job_id': job.id,
                            'action': 'migrate',
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'dry_run': dry_run
                        })
                    else:
                        results['skipped'] += 1
                except Exception as e:
                    logger.error(f"Failed to migrate job {job.id}: {e}")
                    results['failed'] += 1
                    self.migration_log.append({
                        'job_id': job.id,
                        'action': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'dry_run': dry_run
                    })
        
        return results
    
    def _migrate_single_job(self, job: Job, dry_run: bool) -> bool:
        """Migrate a single job to atomic operation patterns."""
        # Check if job needs migration
        if not hasattr(job, 'file_path') or not job.file_path:
            logger.info(f"Job {job.id} has no file path, skipping")
            return False
        
        file_path = Path(job.file_path)
        if not file_path.exists():
            logger.warning(f"Job {job.id} file not found: {job.file_path}")
            return False
        
        # Check if file is already in correct location
        expected_dir = self._get_expected_directory(job)
        if file_path.parent.name == expected_dir:
            logger.info(f"Job {job.id} already in correct location: {expected_dir}")
            return False
        
        if dry_run:
            logger.info(f"DRY RUN: Would migrate job {job.id} from {file_path.parent.name} to {expected_dir}")
            return True
        
        # Perform actual migration using atomic operations
        try:
            # Use atomic service to move file to correct location
            success = self.atomic_service.atomic_move_authoritative(job, job.status)
            if success:
                logger.info(f"Successfully migrated job {job.id} to {expected_dir}")
                return True
            else:
                logger.error(f"Failed to migrate job {job.id}")
                return False
        except Exception as e:
            logger.error(f"Error migrating job {job.id}: {e}")
            return False
    
    def _get_expected_directory(self, job: Job) -> str:
        """Get the expected directory for a job based on its status."""
        return STATUS_TO_DIR.get(job.status, 'Uploaded')
    
    def rollback_migration(self, job_id: Optional[int] = None) -> Dict[str, int]:
        """Rollback migration changes (if needed)."""
        results = {
            'rolled_back': 0,
            'failed': 0,
            'skipped': 0
        }
        
        logger.warning("Rollback functionality not implemented - manual intervention required")
        logger.warning("Check migration log for details of changes made")
        
        return results
    
    def save_migration_log(self, filename: str = None):
        """Save migration log to file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"migration_log_{timestamp}.json"
        
        log_path = Path('logs') / filename
        log_path.parent.mkdir(exist_ok=True)
        
        with open(log_path, 'w') as f:
            json.dump(self.migration_log, f, indent=2)
        
        logger.info(f"Migration log saved to {log_path}")
    
    def generate_migration_report(self) -> str:
        """Generate a migration report."""
        report = []
        report.append("=== Atomic File Operations Migration Report ===")
        report.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"Total operations: {len(self.migration_log)}")
        
        # Count operations by type
        operation_counts = {}
        for entry in self.migration_log:
            action = entry.get('action', 'unknown')
            operation_counts[action] = operation_counts.get(action, 0) + 1
        
        report.append("\nOperation Summary:")
        for action, count in operation_counts.items():
            report.append(f"  {action}: {count}")
        
        if self.migration_log:
            report.append("\nRecent Operations:")
            for entry in self.migration_log[-10:]:  # Last 10 operations
                report.append(f"  {entry['timestamp']} - Job {entry['job_id']} - {entry['action']}")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Migrate to atomic file operations')
    parser.add_argument('--check', action='store_true', help='Check file integrity')
    parser.add_argument('--migrate', action='store_true', help='Migrate files to atomic patterns')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run (default for migrate)')
    parser.add_argument('--rollback', action='store_true', help='Rollback migration changes')
    parser.add_argument('--job-id', type=int, help='Migrate specific job ID only')
    parser.add_argument('--report', action='store_true', help='Generate migration report')
    parser.add_argument('--log-file', help='Save migration log to specified file')
    
    args = parser.parse_args()
    
    if not any([args.check, args.migrate, args.rollback, args.report]):
        parser.print_help()
        return
    
    migration = AtomicFileMigration()
    
    if args.check:
        logger.info("Checking file integrity...")
        issues = migration.check_file_integrity()
        
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        if total_issues == 0:
            logger.info("✅ No integrity issues found")
        else:
            logger.warning(f"⚠️  Found {total_issues} integrity issues:")
            for issue_type, issue_list in issues.items():
                if issue_list:
                    logger.warning(f"  {issue_type}: {len(issue_list)} issues")
                    for issue in issue_list[:5]:  # Show first 5
                        logger.warning(f"    - {issue}")
                    if len(issue_list) > 5:
                        logger.warning(f"    ... and {len(issue_list) - 5} more")
    
    if args.migrate:
        dry_run = args.dry_run if args.dry_run is not None else True
        logger.info(f"Migrating files to atomic patterns (dry_run={dry_run})...")
        results = migration.migrate_job_files(args.job_id, dry_run)
        logger.info(f"Migration results: {results}")
    
    if args.rollback:
        logger.warning("Rollback requested...")
        results = migration.rollback_migration(args.job_id)
        logger.info(f"Rollback results: {results}")
    
    if args.report:
        report = migration.generate_migration_report()
        print(report)
    
    if args.log_file:
        migration.save_migration_log(args.log_file)
    elif any([args.migrate, args.rollback]):
        migration.save_migration_log()

if __name__ == '__main__':
    main()
