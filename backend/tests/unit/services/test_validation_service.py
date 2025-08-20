import pytest
from app.services.validation_service import ValidationService, ValidationResult


def test_validate_staff_required():
    result = ValidationService.validate_staff('')
    assert not result.is_valid
    assert result.error_message == 'staff_name is required'


def test_validate_job_not_found():
    result = ValidationService.validate_job_exists('nonexistent_id')
    assert not result.is_valid
    assert result.error_message == 'Job not found'


def test_validate_status_transition_valid():
    result = ValidationService.validate_status_transition('UPLOADED', 'PENDING')
    assert result.is_valid


def test_validate_status_transition_invalid_source():
    result = ValidationService.validate_status_transition('UNKNOWN', 'PENDING')
    assert not result.is_valid
    assert 'Invalid source status' in result.error_message


def test_validate_status_transition_invalid_target():
    result = ValidationService.validate_status_transition('UPLOADED', 'PRINTING')
    assert not result.is_valid
    assert 'Invalid transition from' in result.error_message
