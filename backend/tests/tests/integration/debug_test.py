#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import tempfile
import json
from pathlib import Path
from app.services.atomic_file_service import get_atomic_file_service

def debug_atomic_operation():
    """Debug atomic file operation."""
    # Create test files
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test file
    file_path = temp_dir / "test_file.txt"
    metadata_path = temp_dir / "test_file_metadata.json"
    
    with open(file_path, 'w') as f:
        f.write("Test content")
    
    metadata = {
        "status": "UPLOADED",
        "file_path": str(file_path),
        "created_at": "2024-01-01T12:00:00Z",
        "size": 12
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    
    # Create target directory
    target_dir = temp_dir / "target"
    target_dir.mkdir()
    target_path = target_dir / file_path.name
    target_metadata_path = target_dir / metadata_path.name
    
    # Get atomic service
    atomic_service = get_atomic_file_service()
    
    try:
        print(f"Source file exists: {file_path.exists()}")
        print(f"Source metadata exists: {metadata_path.exists()}")
        print(f"Target directory exists: {target_dir.exists()}")
        
        # Try atomic move
        with atomic_service.move_file(
            source_path=str(file_path),
            target_path=str(target_path),
            metadata_path=str(metadata_path),
            target_metadata_path=str(target_metadata_path),
            job_id="debug_job"
        ) as operation:
            print(f"Operation ID: {operation.operation_id}")
            print("Operation completed successfully")
        
        print(f"Target file exists: {target_path.exists()}")
        print(f"Target metadata exists: {target_metadata_path.exists()}")
        print(f"Source file exists: {file_path.exists()}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_atomic_operation()
