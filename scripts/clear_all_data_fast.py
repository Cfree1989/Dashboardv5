#!/usr/bin/env python3
"""
FAST Dev script: Clear all jobs, events, payments AND storage files in <1 second.

Usage:
  - python scripts/clear_all_data_fast.py --confirm
  - docker-compose exec backend python scripts/clear_all_data_fast.py --confirm
  - python scripts/clear_all_data_fast.py --confirm --files-only  # Only clear files, not database
"""

import argparse
import os
import sys
import time
import psycopg2
from pathlib import Path
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FAST clear all jobs, events, payments, and storage files")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--files-only", action="store_true", help="Only clear storage files, not database")
    parser.add_argument("--db-only", action="store_true", help="Only clear database, not storage files")
    return parser.parse_args()


def get_db_connection():
    """Get direct PostgreSQL connection bypassing Flask/SQLAlchemy overhead."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
    )


def clear_storage_files() -> dict:
    """Clear all files from storage directories using pathlib for cross-platform compatibility."""
    storage_root = Path(os.environ.get('STORAGE_PATH', 'storage'))
    
    # Define storage directories to clean
    storage_dirs = [
        'Uploaded', 'Pending', 'ReadyToPrint', 'Printing', 
        'Completed', 'PaidPickedUp', 'Rejected', 'Archived'
    ]
    
    files_deleted = 0
    dirs_cleaned = 0
    
    for dir_name in storage_dirs:
        dir_path = storage_root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            # Count files before deletion
            files_in_dir = list(dir_path.iterdir())
            file_count = len([f for f in files_in_dir if f.is_file()])
            
            if file_count > 0:
                # Delete all files in directory (keep directory structure)
                for file_path in files_in_dir:
                    if file_path.is_file():
                        try:
                            file_path.unlink()  # pathlib's delete method
                            files_deleted += 1
                        except Exception as e:
                            print(f"⚠️  Failed to delete {file_path}: {e}")
                
                dirs_cleaned += 1
    
    return {
        'files_deleted': files_deleted,
        'dirs_cleaned': dirs_cleaned,
        'storage_root': str(storage_root)
    }


def main() -> int:
    args = parse_args()
    
    # Validate arguments
    if args.files_only and args.db_only:
        print("❌ Cannot use --files-only and --db-only together")
        return 1
    
    # Check database requirement for non-files-only operations
    if not args.files_only and "DATABASE_URL" not in os.environ:
        print("❌ DATABASE_URL not set. Run inside backend container or set env var.")
        return 1

    # Confirmation prompt
    if not args.confirm:
        if args.files_only:
            action = "delete ALL storage files"
        elif args.db_only:
            action = "delete ALL database records (jobs, events, payments)"
        else:
            action = "delete ALL database records AND storage files"
            
        print(f"This will {action}. Type 'DELETE ALL' to confirm:")
        try:
            confirmation = input().strip()
        except KeyboardInterrupt:
            return 1
        if confirmation != "DELETE ALL":
            print("Cancelled.")
            return 0

    start_time = time.time()
    
    try:
        # Files-only mode
        if args.files_only:
            print("🗂️  Clearing storage files...")
            file_result = clear_storage_files()
            elapsed = time.time() - start_time
            print("✅ Storage cleanup completed:")
            print(f"  files deleted: {file_result['files_deleted']}")
            print(f"  directories cleaned: {file_result['dirs_cleaned']}")
            print(f"  storage root: {file_result['storage_root']}")
            print(f"⚡ Completed in {elapsed:.3f} seconds")
            return 0
        
        # Database operations
        db_result = None
        if not args.db_only:  # Clear files unless db-only mode
            print("🗂️  Clearing storage files...")
            file_result = clear_storage_files()
            print(f"📁 Cleared {file_result['files_deleted']} files from {file_result['dirs_cleaned']} directories")
        
        if not args.files_only:  # Clear database unless files-only mode
            print("🗄️  Clearing database...")
            # Direct PostgreSQL connection - no Flask overhead
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get counts first (optional - comment out for max speed)
                    cur.execute("SELECT COUNT(*) FROM payment")
                    payment_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM event") 
                    event_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM job")
                    job_count = cur.fetchone()[0]
                    
                    print(f"Before: jobs={job_count}, events={event_count}, payments={payment_count}")
                    
                    # FAST DELETE: Raw SQL in single transaction
                    # Order matters due to foreign key constraints
                    cur.execute("DELETE FROM payment")
                    deleted_payments = cur.rowcount
                    
                    cur.execute("DELETE FROM event")
                    deleted_events = cur.rowcount
                    
                    cur.execute("DELETE FROM job")  
                    deleted_jobs = cur.rowcount
                    
                    # Single commit for all operations
                    conn.commit()
                    
                    db_result = {
                        'jobs': deleted_jobs,
                        'events': deleted_events,
                        'payments': deleted_payments
                    }
        
        elapsed = time.time() - start_time
        print("✅ Cleanup completed:")
        
        if not args.db_only and 'file_result' in locals():
            print(f"  📁 files deleted: {file_result['files_deleted']}")
            print(f"  📁 directories cleaned: {file_result['dirs_cleaned']}")
            
        if db_result:
            print(f"  🗄️  jobs: {db_result['jobs']}")
            print(f"  🗄️  events: {db_result['events']}")
            print(f"  🗄️  payments: {db_result['payments']}")
            
        print(f"⚡ Completed in {elapsed:.3f} seconds")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
