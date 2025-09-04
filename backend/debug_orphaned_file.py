#!/usr/bin/env python3
"""
Debug script to identify orphaned file and test cleanup functionality
"""

import sys
import os
import json
from pathlib import Path

# Add the backend app to the path
sys.path.insert(0, '/app')

from app import create_app, db
from app.routes.admin import perform_audit
from app.models import Job

def main():
    app = create_app()
    
    with app.app_context():
        print("=== ORPHANED FILE DIAGNOSIS ===")
        
        # Get audit report
        try:
            audit_result = perform_audit()
            print(f"\n1. AUDIT RESULTS:")
            print(json.dumps(audit_result, indent=2))
            
            # Check database state
            print(f"\n2. DATABASE STATE:")
            all_jobs = Job.query.all()
            print(f"Total jobs in database: {len(all_jobs)}")
            for job in all_jobs:
                print(f"  Job {job.id}: {job.file_path} | {job.metadata_path}")
            
            # Check storage files manually
            print(f"\n3. STORAGE FILE SCAN:")
            storage_root = Path('/app/storage')
            all_files = []
            for subdir in ['Uploaded', 'Pending', 'ReadyToPrint', 'Printing', 'Completed', 'PaidPickedUp', 'Archived', 'Rejected']:
                dir_path = storage_root / subdir
                if dir_path.exists():
                    for file_path in dir_path.glob('*'):
                        if file_path.is_file():
                            all_files.append(str(file_path))
                            
            # Check root directory too
            for file_path in storage_root.glob('*'):
                if file_path.is_file():
                    all_files.append(str(file_path))
            
            print(f"Files found in storage: {len(all_files)}")
            for f in all_files:
                print(f"  {f}")
                
            # Identify the specific orphaned file
            if audit_result.get('orphaned_files'):
                print(f"\n4. ORPHANED FILE DETAILS:")
                for orphan_path in audit_result['orphaned_files']:
                    orphan = Path(orphan_path)
                    print(f"  Path: {orphan_path}")
                    print(f"  Exists: {orphan.exists()}")
                    if orphan.exists():
                        print(f"  Size: {orphan.stat().st_size} bytes")
                        print(f"  Permissions: {oct(orphan.stat().st_mode)}")
                        try:
                            with open(orphan, 'r') as f:
                                content_preview = f.read(100)
                                print(f"  Content preview: {repr(content_preview)}")
                        except:
                            print(f"  Content: <binary or unreadable>")
                            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
