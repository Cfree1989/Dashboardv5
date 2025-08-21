#!/usr/bin/env python3
"""
Simple integration tests to verify system functionality.
"""

import pytest
import requests
import time

class TestSimpleIntegration:
    """Simple integration tests that don't hit rate limits."""
    
    def test_health_endpoint(self):
        """Test that the health endpoint is working."""
        response = requests.get("http://localhost:5000/health")
        assert response.status_code == 200, "Health endpoint should be accessible"
        print("✅ Health endpoint working")
    
    def test_catalog_endpoint(self):
        """Test that the catalog endpoint returns valid data."""
        response = requests.get("http://localhost:5000/api/v1/catalog")
        assert response.status_code == 200, "Catalog endpoint should be accessible"
        
        data = response.json()
        assert 'data' in data, "Catalog should have data field"
        assert 'materials' in data['data'], "Catalog should have materials"
        assert 'printers' in data['data'], "Catalog should have printers"
        
        print("✅ Catalog endpoint working")
    
    def test_submit_endpoint_validation(self):
        """Test that submit endpoint validates input without hitting rate limit."""
        # Test without file (should fail validation, not rate limit)
        response = requests.post("http://localhost:5000/api/v1/submit")
        assert response.status_code == 400, "Should fail validation without file"
        
        response_data = response.json()
        assert 'error' in response_data, "Should return error message"
        assert 'file is required' in response_data['error'], "Should mention file requirement"
        
        print("✅ Submit endpoint validation working")
    
    def test_system_status(self):
        """Test overall system status."""
        # Check all critical endpoints
        endpoints = [
            ("/health", "Health"),
            ("/api/v1/catalog", "Catalog"),
        ]
        
        for endpoint, name in endpoints:
            response = requests.get(f"http://localhost:5000{endpoint}")
            assert response.status_code == 200, f"{name} endpoint should be accessible"
            print(f"✅ {name} endpoint working")
        
        print("✅ All critical endpoints accessible")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
