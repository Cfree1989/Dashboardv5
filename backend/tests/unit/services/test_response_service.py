from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode
import pytest
from datetime import datetime

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
    assert 'error' in response.json
    assert response.json['error']['message'] == 'Something went wrong'
    assert response.json['error']['code'] == ErrorCode.INVALID_INPUT.value
    assert response.json['error']['category'] == ErrorCategory.VALIDATION.value
    assert 'timestamp' in response.json['error']
    assert response.json['error']['status'] == 400

def test_error_with_custom_status():
    """Test error response with custom status"""
    response, status = ResponseService.error('Not found', 404)
    assert status == 404
    assert response.json['error']['message'] == 'Not found'
    assert response.json['error']['code'] == ErrorCode.RESOURCE_NOT_FOUND.value
    assert response.json['error']['category'] == ErrorCategory.BUSINESS_LOGIC.value

def test_error_with_custom_code_and_category():
    """Test error response with custom error code and category"""
    response, status = ResponseService.error(
        'Custom error',
        status=422,
        error_code=ErrorCode.BUSINESS_RULE_VIOLATION.value,
        category=ErrorCategory.BUSINESS_LOGIC
    )
    assert status == 422
    assert response.json['error']['message'] == 'Custom error'
    assert response.json['error']['code'] == ErrorCode.BUSINESS_RULE_VIOLATION.value
    assert response.json['error']['category'] == ErrorCategory.BUSINESS_LOGIC.value

def test_error_with_details():
    """Test error response with additional details"""
    details = {'field': 'email', 'constraint': 'must be valid email'}
    response, status = ResponseService.error('Validation failed', 400, details=details)
    assert status == 400
    assert response.json['error']['message'] == 'Validation failed'
    assert response.json['error']['details'] == details

def test_error_with_field():
    """Test error response with field information"""
    response, status = ResponseService.error('Invalid email', 400, field='email')
    assert status == 400
    assert response.json['error']['message'] == 'Invalid email'
    assert response.json['error']['field'] == 'email'

def test_error_with_timestamp():
    """Test error response with custom timestamp"""
    timestamp = '2023-01-01T12:00:00Z'
    response, status = ResponseService.error('Test error', timestamp=timestamp)
    assert status == 400
    assert response.json['error']['timestamp'] == timestamp

def test_not_found_default():
    """Test not found response with default resource name"""
    response, status = ResponseService.not_found()
    assert status == 404
    assert response.json['error']['message'] == 'Resource not found'
    assert response.json['error']['code'] == ErrorCode.RESOURCE_NOT_FOUND.value
    assert response.json['error']['category'] == ErrorCategory.BUSINESS_LOGIC.value

def test_not_found_custom():
    """Test not found response with custom resource name"""
    response, status = ResponseService.not_found('Job')
    assert status == 404
    assert response.json['error']['message'] == 'Job not found'

def test_not_found_with_custom_code():
    """Test not found response with custom error code"""
    response, status = ResponseService.not_found('Job', ErrorCode.JOB_NOT_FOUND.value)
    assert status == 404
    assert response.json['error']['code'] == ErrorCode.JOB_NOT_FOUND.value

def test_validation_error_basic():
    """Test validation error response without field"""
    response, status = ResponseService.validation_error('Invalid input')
    assert status == 400
    assert response.json['error']['message'] == 'Invalid input'
    assert response.json['error']['code'] == ErrorCode.INVALID_INPUT.value
    assert response.json['error']['category'] == ErrorCategory.VALIDATION.value

def test_validation_error_with_field():
    """Test validation error response with field"""
    response, status = ResponseService.validation_error('Required field', 'email')
    assert status == 400
    assert response.json['error']['message'] == 'Required field'
    assert response.json['error']['field'] == 'email'

def test_validation_error_with_custom_code():
    """Test validation error response with custom error code"""
    response, status = ResponseService.validation_error(
        'Invalid format', 
        error_code=ErrorCode.INVALID_FORMAT.value
    )
    assert status == 400
    assert response.json['error']['code'] == ErrorCode.INVALID_FORMAT.value

def test_validation_error_with_details():
    """Test validation error response with details"""
    details = {'min_length': 3, 'max_length': 50}
    response, status = ResponseService.validation_error(
        'Invalid length', 
        details=details
    )
    assert status == 400
    assert response.json['error']['details'] == details

def test_unauthorized_default():
    """Test unauthorized response with default message"""
    response, status = ResponseService.unauthorized()
    assert status == 401
    assert response.json['error']['message'] == 'Unauthorized'
    assert response.json['error']['code'] == ErrorCode.UNAUTHORIZED.value
    assert response.json['error']['category'] == ErrorCategory.AUTHENTICATION.value

def test_unauthorized_custom():
    """Test unauthorized response with custom message"""
    response, status = ResponseService.unauthorized('Invalid token')
    assert status == 401
    assert response.json['error']['message'] == 'Invalid token'

def test_unauthorized_with_custom_code():
    """Test unauthorized response with custom error code"""
    response, status = ResponseService.unauthorized('Token expired', ErrorCode.TOKEN_EXPIRED.value)
    assert status == 401
    assert response.json['error']['code'] == ErrorCode.TOKEN_EXPIRED.value

def test_forbidden_default():
    """Test forbidden response with default message"""
    response, status = ResponseService.forbidden()
    assert status == 403
    assert response.json['error']['message'] == 'Forbidden'
    assert response.json['error']['code'] == ErrorCode.FORBIDDEN.value
    assert response.json['error']['category'] == ErrorCategory.AUTHORIZATION.value

def test_forbidden_custom():
    """Test forbidden response with custom message"""
    response, status = ResponseService.forbidden('Insufficient permissions')
    assert status == 403
    assert response.json['error']['message'] == 'Insufficient permissions'

def test_forbidden_with_custom_code():
    """Test forbidden response with custom error code"""
    response, status = ResponseService.forbidden('No access', ErrorCode.INSUFFICIENT_PERMISSIONS.value)
    assert status == 403
    assert response.json['error']['code'] == ErrorCode.INSUFFICIENT_PERMISSIONS.value

def test_conflict():
    """Test conflict response"""
    response, status = ResponseService.conflict('Resource already exists')
    assert status == 409
    assert response.json['error']['message'] == 'Resource already exists'
    assert response.json['error']['code'] == ErrorCode.RESOURCE_CONFLICT.value
    assert response.json['error']['category'] == ErrorCategory.BUSINESS_LOGIC.value

def test_conflict_with_custom_code():
    """Test conflict response with custom error code"""
    response, status = ResponseService.conflict(
        'Job already locked', 
        ErrorCode.JOB_ALREADY_LOCKED.value
    )
    assert status == 409
    assert response.json['error']['code'] == ErrorCode.JOB_ALREADY_LOCKED.value

def test_conflict_with_details():
    """Test conflict response with details"""
    details = {'locked_by': 'user123', 'locked_until': '2023-01-01T12:00:00Z'}
    response, status = ResponseService.conflict('Job locked', details=details)
    assert status == 409
    assert response.json['error']['details'] == details

def test_business_error():
    """Test business logic error response"""
    response, status = ResponseService.business_error('Invalid status transition')
    assert status == 422
    assert response.json['error']['message'] == 'Invalid status transition'
    assert response.json['error']['code'] == ErrorCode.BUSINESS_RULE_VIOLATION.value
    assert response.json['error']['category'] == ErrorCategory.BUSINESS_LOGIC.value

def test_business_error_with_custom_code():
    """Test business logic error response with custom error code"""
    response, status = ResponseService.business_error(
        'Invalid transition', 
        ErrorCode.INVALID_STATUS_TRANSITION.value
    )
    assert status == 422
    assert response.json['error']['code'] == ErrorCode.INVALID_STATUS_TRANSITION.value

def test_server_error_default():
    """Test server error response with default message"""
    response, status = ResponseService.server_error()
    assert status == 500
    assert response.json['error']['message'] == 'Internal server error'
    assert response.json['error']['code'] == ErrorCode.INTERNAL_SERVER_ERROR.value
    assert response.json['error']['category'] == ErrorCategory.SYSTEM.value

def test_server_error_custom():
    """Test server error response with custom message"""
    response, status = ResponseService.server_error('Database connection failed')
    assert status == 500
    assert response.json['error']['message'] == 'Database connection failed'

def test_server_error_with_custom_code():
    """Test server error response with custom error code"""
    response, status = ResponseService.server_error(
        'Database error', 
        ErrorCode.DATABASE_ERROR.value
    )
    assert status == 500
    assert response.json['error']['code'] == ErrorCode.DATABASE_ERROR.value

def test_server_error_with_details():
    """Test server error response with details"""
    details = {'database': 'postgresql', 'operation': 'insert'}
    response, status = ResponseService.server_error('Database error', details=details)
    assert status == 500
    assert response.json['error']['details'] == details

def test_file_operation_error():
    """Test file operation error response"""
    response, status = ResponseService.file_operation_error('File upload failed')
    assert status == 500
    assert response.json['error']['message'] == 'File upload failed'
    assert response.json['error']['code'] == ErrorCode.FILE_OPERATION_ERROR.value
    assert response.json['error']['category'] == ErrorCategory.FILE_OPERATION.value

def test_file_operation_error_with_details():
    """Test file operation error response with details"""
    details = {'file_path': '/path/to/file.stl', 'operation': 'upload'}
    response, status = ResponseService.file_operation_error('File operation failed', details)
    assert status == 500
    assert response.json['error']['details'] == details

def test_database_error():
    """Test database error response"""
    response, status = ResponseService.database_error('Connection timeout')
    assert status == 500
    assert response.json['error']['message'] == 'Connection timeout'
    assert response.json['error']['code'] == ErrorCode.DATABASE_ERROR.value
    assert response.json['error']['category'] == ErrorCategory.DATABASE.value

def test_database_error_with_details():
    """Test database error response with details"""
    details = {'query': 'SELECT * FROM jobs', 'params': {'id': 123}}
    response, status = ResponseService.database_error('Query failed', details)
    assert status == 500
    assert response.json['error']['details'] == details

def test_error_codes_enum():
    """Test that all error codes are properly defined"""
    assert ErrorCode.INVALID_INPUT.value == "INVALID_INPUT"
    assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
    assert ErrorCode.FORBIDDEN.value == "FORBIDDEN"
    assert ErrorCode.RESOURCE_NOT_FOUND.value == "RESOURCE_NOT_FOUND"
    assert ErrorCode.RESOURCE_CONFLICT.value == "RESOURCE_CONFLICT"
    assert ErrorCode.BUSINESS_RULE_VIOLATION.value == "BUSINESS_RULE_VIOLATION"
    assert ErrorCode.INTERNAL_SERVER_ERROR.value == "INTERNAL_SERVER_ERROR"

def test_error_categories_enum():
    """Test that all error categories are properly defined"""
    assert ErrorCategory.VALIDATION.value == "validation"
    assert ErrorCategory.AUTHENTICATION.value == "authentication"
    assert ErrorCategory.AUTHORIZATION.value == "authorization"
    assert ErrorCategory.BUSINESS_LOGIC.value == "business_logic"
    assert ErrorCategory.SYSTEM.value == "system"
    assert ErrorCategory.FILE_OPERATION.value == "file_operation"
    assert ErrorCategory.DATABASE.value == "database"
