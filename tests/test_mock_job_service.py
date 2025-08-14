"""
Tests for MockJobService pricing calculations and job generation.
"""

import pytest
from app.services.mock_job_service import MockJobService
from app import create_app, db
from app.models.job import Job
from app.models.payment import Payment


def test_pricing_calculation_filament():
    """Test filament pricing calculation."""
    # Test normal pricing
    assert MockJobService.calculate_price(50.0, 'Filament') == 500  # $5.00
    assert MockJobService.calculate_price(25.0, 'Filament') == 250  # $2.50
    
    # Test minimum charge
    assert MockJobService.calculate_price(10.0, 'Filament') == 300  # $3.00 minimum
    assert MockJobService.calculate_price(5.0, 'Filament') == 300   # $3.00 minimum


def test_pricing_calculation_resin():
    """Test resin pricing calculation."""
    # Test normal pricing
    assert MockJobService.calculate_price(25.0, 'Resin') == 500  # $5.00
    assert MockJobService.calculate_price(15.0, 'Resin') == 300  # $3.00
    
    # Test minimum charge
    assert MockJobService.calculate_price(10.0, 'Resin') == 300  # $3.00 minimum
    assert MockJobService.calculate_price(5.0, 'Resin') == 300   # $3.00 minimum


def test_pricing_calculation_edge_cases():
    """Test edge cases in pricing calculation."""
    # Zero weight should still get minimum charge
    assert MockJobService.calculate_price(0.0, 'Filament') == 300
    assert MockJobService.calculate_price(0.0, 'Resin') == 300
    
    # Very small weights
    assert MockJobService.calculate_price(0.1, 'Filament') == 300  # $0.01 < $3.00
    assert MockJobService.calculate_price(0.1, 'Resin') == 300     # $0.02 < $3.00
    
    # Exact minimum charge thresholds
    assert MockJobService.calculate_price(30.0, 'Filament') == 300  # $3.00 exactly
    assert MockJobService.calculate_price(15.0, 'Resin') == 300     # $3.00 exactly


def test_generate_mock_jobs_api(client, token):
    """Test the mock jobs API endpoint."""
    # Test with valid request
    data = {
        'counts': {
            'UPLOADED': 2,
            'COMPLETED': 1
        },
        'email': 'cfree3@lsu.edu',
        'addNotes': True
    }
    
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['message'].startswith('Successfully generated')
    assert result['created_counts']['UPLOADED'] == 2
    assert result['created_counts']['COMPLETED'] == 1
    assert result['student_email'] == 'cfree3@lsu.edu'


def test_generate_mock_jobs_with_payments(client, token):
    """Test generating jobs with payments."""
    data = {
        'counts': {
            'PAIDPICKEDUP': 2
        },
        'email': 'cfree3@lsu.edu'
    }
    
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    
    # Verify jobs were created with payments
    app = create_app()
    with app.app_context():
        paid_jobs = Job.query.filter_by(status='PAIDPICKEDUP').all()
        assert len(paid_jobs) >= 2
        
        for job in paid_jobs:
            assert job.student_email == 'cfree3@lsu.edu'
            assert job.payment is not None
            # Verify payment has correct pricing
            expected_price = MockJobService.calculate_price(job.payment.grams, job.material)
            assert job.payment.price_cents == expected_price


def test_generate_mock_jobs_validation(client, token):
    """Test validation of mock jobs API."""
    # Test invalid status
    data = {'counts': {'INVALID': 1}}
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    
    # Test invalid count
    data = {'counts': {'UPLOADED': -1}}
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    
    # Test count too high
    data = {'counts': {'UPLOADED': 100}}
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    
    # Test invalid email
    data = {'counts': {'UPLOADED': 1}, 'email': 'invalid-email'}
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400


def test_mock_job_diversity(client, token):
    """Test that generated jobs have diverse characteristics."""
    data = {
        'counts': {
            'UPLOADED': 10,
            'COMPLETED': 5
        },
        'email': 'cfree3@lsu.edu'
    }
    
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    
    app = create_app()
    with app.app_context():
        jobs = Job.query.filter_by(student_email='cfree3@lsu.edu').all()
        
        # Check for diversity in materials
        materials = [job.material for job in jobs]
        assert 'Filament' in materials
        assert 'Resin' in materials
        
        # Check for diversity in disciplines
        disciplines = [job.discipline for job in jobs]
        assert len(set(disciplines)) > 1
        
        # Check for diversity in printers
        printers = [job.printer for job in jobs]
        assert len(set(printers)) > 1
        
        # Check that all jobs have the correct email
        for job in jobs:
            assert job.student_email == 'cfree3@lsu.edu'


def test_mock_job_notes(client, token):
    """Test that notes are added when requested."""
    # Test with notes enabled
    data = {
        'counts': {'UPLOADED': 5},
        'addNotes': True
    }
    
    response = client.post(
        '/api/v1/admin/mock-jobs',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    
    app = create_app()
    with app.app_context():
        jobs_with_notes = Job.query.filter(
            Job.student_email == 'cfree3@lsu.edu',
            Job.notes.isnot(None)
        ).count()
        
        # Should have some jobs with notes
        assert jobs_with_notes > 0
