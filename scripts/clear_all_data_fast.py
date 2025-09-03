#!/usr/bin/env python3
"""
FAST Dev script: Clear all jobs, events, and payments in <1 second.

Usage:
  - python scripts/clear_all_data_fast.py --confirm
  - docker-compose exec backend python scripts/clear_all_data_fast.py --confirm
"""

import argparse
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FAST clear all jobs, events, and payments")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
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


def main() -> int:
    if "DATABASE_URL" not in os.environ:
        print("❌ DATABASE_URL not set. Run inside backend container or set env var.")
        return 1

    args = parse_args()
    if not args.confirm:
        print("This will delete ALL jobs, events, and payments. Type 'DELETE ALL' to confirm:")
        try:
            confirmation = input().strip()
        except KeyboardInterrupt:
            return 1
        if confirmation != "DELETE ALL":
            print("Cancelled.")
            return 0

    start_time = time.time()
    
    try:
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
                
                elapsed = time.time() - start_time
                print("✅ Deleted:")
                print(f"  jobs: {deleted_jobs}")
                print(f"  events: {deleted_events}")
                print(f"  payments: {deleted_payments}")
                print(f"⚡ Completed in {elapsed:.3f} seconds")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
