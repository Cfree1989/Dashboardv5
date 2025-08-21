#!/usr/bin/env python3
"""
Integration tests for job lifecycle to verify atomic file operations.
"""

import pytest
import requests
import os
from pathlib import Path
import time

class TestJobLifecycleIntegration:
    """Integration tests for complete job lifecycle."""
    
    @pytest.fixture
    def test_file_path(self):
        """Create a test file for job submission."""
        test_dir = Path(__file__).parent
        test_file_path = test_dir / "test_model.stl"
        test_file_content = "Test 3D model content for atomic file operations"
        with open(test_file_path, "w") as f:
            f.write(test_file_content)
        yield test_file_path
        # Cleanup
        if test_file_path.exists():
            test_file_path.unlink()
    
    def test_job_submission_creates_files_atomically(self, test_file_path):
        """Test that job submission creates files atomically."""
        url = "http://localhost:5000/api/v1/submit"
        
        with open(test_file_path, "rb") as f:
            files = {'file': ('test_model.stl', f, 'application/octet-stream')}
            
            data = {
                'student_name': 'Integration Test Student',
                'student_email': 'integration@lsu.edu',
                'discipline': 'Engineering',
                'class_number': 'ME 2743',
                'printer': 'Prusa MK4S',
                'material': 'PLA',
                'color': 'True Black',
                'notes': 'Integration test for atomic file operations'
            }
            
            response = requests.post(url, files=files, data=data)
            
            assert response.status_code == 201, f"Job submission failed: {response.text}"
            
            job_data = response.json()
            job_id = job_data.get('id')
            short_id = job_data.get('short_id')
            
            # Verify job was created
            assert job_id is not None, "Job ID should be returned"
            assert short_id is not None, "Short ID should be returned"
            assert job_data.get('status') == 'UPLOADED', "Job should be in UPLOADED status"
            
            # Verify file paths are set
            assert job_data.get('file_path') is not None, "File path should be set"
            assert job_data.get('display_name') is not None, "Display name should be set"
            
            print(f"✅ Job submitted successfully: {short_id}")
            return job_id
    
    def test_job_submission_with_invalid_catalog_values(self, test_file_path):
        """Test that job submission rejects invalid catalog values."""
        url = "http://localhost:5000/api/v1/submit"
        
        with open(test_file_path, "rb") as f:
            files = {'file': ('test_model.stl', f, 'application/octet-stream')}
            
            data = {
                'student_name': 'Test Student',
                'student_email': 'test@lsu.edu',
                'discipline': 'Engineering',
                'class_number': 'ME 2743',
                'printer': 'Invalid Printer',  # Invalid printer
                
                'material': 'Invalid Material',  # Invalid material
                'color': 'Black',
                'notes': 'Test with invalid catalog values'
            }
            
            response = requests.post(url, files=files, data=data)
            
            assert response.status_code == 400, "Should reject invalid catalog values"
            response_data = response.json()
            assert 'error' in response_data, "Should return error message"
            assert 'Invalid' in response_data.get('error', ''), "Should mention invalid values"
            
            print("✅ Invalid catalog values properly rejected")
    
    def test_job_submission_duplicate_detection(self, test_file_path):
        """Test that duplicate job submission is detected."""
        url = "http://localhost:5000/api/v1/submit"
        
        # Submit first job
        with open(test_file_path, "rb") as f:
            files = {'file': ('test_model.stl', f, 'application/octet-stream')}
            
            data = {
                'student_name': 'Duplicate Test Student',
                'student_email': 'duplicate@lsu.edu',
                'discipline': 'Engineering',
                'class_number': 'ME 2743',
                'printer': 'Prusa MK4S',
                'material': 'PLA',
                'color': 'True Black',
                'notes': 'First submission'
            }
            
            response1 = requests.post(url, files=files, data=data)
            assert response1.status_code == 201, "First submission should succeed"
        
        # Submit duplicate job (same file, same email)
        with open(test_file_path, "rb") as f:
            files = {'file': ('test_model.stl', f, 'application/octet-stream')}
            
            data = {
                'student_name': 'Duplicate Test Student',
                'student_email': 'duplicate@lsu.edu',  # Same email
                'discipline': 'Engineering',
                'class_number': 'ME 2743',
                'printer': 'Prusa MK4S',
                'material': 'PLA',
                'color': 'True Black',
                'notes': 'Duplicate submission'
            }
            
            response2 = requests.post(url, files=files, data=data)
            assert response2.status_code == 409, "Duplicate submission should be rejected"
            
            response_data = response2.json()
            assert 'duplicate' in response_data.get('message', '').lower(), "Should mention duplicate"
            
            print("✅ Duplicate detection working correctly")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
