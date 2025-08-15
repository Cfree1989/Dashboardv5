#!/usr/bin/env python3
"""
Integration test script for job submission to verify atomic file operations.
"""

import requests
import os
from pathlib import Path

def test_job_submission():
    """Test job submission with a file to verify atomic file operations."""
    
    # Get the directory where this test script is located
    test_dir = Path(__file__).parent
    
    # Create a test file in the test directory
    test_file_path = test_dir / "test_model.stl"
    test_file_content = "Test 3D model content for atomic file operations"
    with open(test_file_path, "w") as f:
        f.write(test_file_content)
    
    # Prepare the form data
    url = "http://localhost:5000/api/v1/submit"
    
    with open(test_file_path, "rb") as f:
        files = {'file': ('test_model.stl', f, 'application/octet-stream')}
        
        data = {
            'student_name': 'Test Student',
            'student_email': 'test@lsu.edu',
            'discipline': 'Engineering',
            'class_number': 'ME 2743',
            'printer': 'Prusa MK3S',
            'material': 'PLA',
            'color': 'Black',
            'notes': 'Test job for atomic file operations'
        }
        
        print("Submitting test job...")
        response = requests.post(url, files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Job submitted successfully!")
            job_data = response.json()
            print(f"Job ID: {job_data.get('id')}")
            print(f"Short ID: {job_data.get('short_id')}")
            return job_data.get('id')
        else:
            print("❌ Job submission failed!")
            return None

if __name__ == "__main__":
    test_job_submission()
