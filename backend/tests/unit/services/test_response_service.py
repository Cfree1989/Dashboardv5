import pytest
from app.services.response_service import ResponseService

def test_success_with_data():
    """Test success response with data"""
    response, status = ResponseService.success({'key': 'value'})
    assert status == 200
    assert response.json == {'key': 'value'}

def test_success_without_data():
    """Test success response without data"""
    response, status = ResponseService.success()
    assert status == 200
    assert response.json == {}

def test_success_with_custom_status():
    """Test success response with custom status"""
    response, status = ResponseService.success({'created': True}, 201)
    assert status == 201
    assert response.json == {'created': True}

def test_error_basic():
    """Test basic error response"""
    response, status = ResponseService.error('Something went wrong')
    assert status == 400
    assert response.json == {'message': 'Something went wrong'}

def test_error_with_custom_status():
    """Test error response with custom status"""
    response, status = ResponseService.error('Not found', 404)
    assert status == 404
    assert response.json == {'message': 'Not found'}

def test_error_with_details():
    """Test error response with additional details"""
    details = {'field': 'email', 'code': 'INVALID_FORMAT'}
    response, status = ResponseService.error('Validation failed', 400, details)
    assert status == 400
    assert response.json == {
        'message': 'Validation failed',
        'field': 'email',
        'code': 'INVALID_FORMAT'
    }

def test_not_found_default():
    """Test not found response with default resource name"""
    response, status = ResponseService.not_found()
    assert status == 404
    assert response.json == {'message': 'Resource not found'}

def test_not_found_custom():
    """Test not found response with custom resource name"""
    response, status = ResponseService.not_found('Job')
    assert status == 404
    assert response.json == {'message': 'Job not found'}

def test_validation_error_basic():
    """Test validation error response without field"""
    response, status = ResponseService.validation_error('Invalid input')
    assert status == 400
    assert response.json == {'message': 'Invalid input'}

def test_validation_error_with_field():
    """Test validation error response with field"""
    response, status = ResponseService.validation_error('Required field', 'email')
    assert status == 400
    assert response.json == {'message': 'Required field', 'field': 'email'}

def test_unauthorized_default():
    """Test unauthorized response with default message"""
    response, status = ResponseService.unauthorized()
    assert status == 401
    assert response.json == {'message': 'Unauthorized'}

def test_unauthorized_custom():
    """Test unauthorized response with custom message"""
    response, status = ResponseService.unauthorized('Invalid credentials')
    assert status == 401
    assert response.json == {'message': 'Invalid credentials'}

def test_forbidden_default():
    """Test forbidden response with default message"""
    response, status = ResponseService.forbidden()
    assert status == 403
    assert response.json == {'message': 'Forbidden'}

def test_forbidden_custom():
    """Test forbidden response with custom message"""
    response, status = ResponseService.forbidden('Insufficient permissions')
    assert status == 403
    assert response.json == {'message': 'Insufficient permissions'}

def test_server_error_default():
    """Test server error response with default message"""
    response, status = ResponseService.server_error()
    assert status == 500
    assert response.json == {'message': 'Internal server error'}

def test_server_error_custom():
    """Test server error response with custom message"""
    response, status = ResponseService.server_error('Database connection failed')
    assert status == 500
    assert response.json == {'message': 'Database connection failed'}
