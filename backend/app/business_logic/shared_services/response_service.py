# backend/app/services/response_service.py
from flask import jsonify
from typing import Any, Dict, Optional, Tuple, List
from enum import Enum
import json
from datetime import datetime, timezone

class ErrorCategory(Enum):
    """Error categories for classification and routing."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    FILE_OPERATION = "file_operation"
    DATABASE = "database"
    NETWORK = "network"

class ErrorCode(Enum):
    """Standard error codes for consistent error handling."""
    # Validation errors (400)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_VALUE = "INVALID_VALUE"
    
    # Authentication errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Authorization errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Not found errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    
    # Conflict errors (409)
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    JOB_ALREADY_LOCKED = "JOB_ALREADY_LOCKED"
    DUPLICATE_SUBMISSION = "DUPLICATE_SUBMISSION"
    
    # Business logic errors (422)
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # System errors (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    FILE_OPERATION_ERROR = "FILE_OPERATION_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

class ResponseService:
    @staticmethod
    def _safe_jsonify(data: Any):
        """Safely create JSON response, handling Flask context"""
        try:
            return jsonify(data)
        except RuntimeError:
            # Outside Flask context (e.g., in tests) - create Response-like object
            from flask import Response
            return Response(json.dumps(data), mimetype='application/json')
    
    @staticmethod
    def success(data: Any = None, status: int = 200) -> Tuple[Any, int]:
        """Standard success response - returns tuple for Flask compatibility"""
        if data is not None:
            return ResponseService._safe_jsonify(data), status
        else:
            return ResponseService._safe_jsonify({}), status
    
    @staticmethod
    def error(
        message: str, 
        status: int = 400, 
        error_code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        details: Optional[Dict] = None,
        field: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> Tuple[Any, int]:
        """
        Standard error response with comprehensive error information.
        
        Args:
            message: Human-readable error message
            status: HTTP status code
            error_code: Machine-readable error code
            category: Error category for classification
            details: Additional error details
            field: Field name if validation error
            timestamp: Error timestamp (auto-generated if not provided)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        response_data = {
            'error': {
                'message': message,
                'code': error_code or ResponseService._get_default_error_code(status),
                'category': category.value if category else ResponseService._get_default_category(status),
                'timestamp': timestamp,
                'status': status
            }
        }
        
        if field:
            response_data['error']['field'] = field
            
        if details:
            response_data['error']['details'] = details
            
        return ResponseService._safe_jsonify(response_data), status
    
    @staticmethod
    def _get_default_error_code(status: int) -> str:
        """Get default error code based on HTTP status."""
        status_to_code = {
            400: ErrorCode.INVALID_INPUT.value,
            401: ErrorCode.UNAUTHORIZED.value,
            403: ErrorCode.FORBIDDEN.value,
            404: ErrorCode.RESOURCE_NOT_FOUND.value,
            409: ErrorCode.RESOURCE_CONFLICT.value,
            422: ErrorCode.BUSINESS_RULE_VIOLATION.value,
            500: ErrorCode.INTERNAL_SERVER_ERROR.value
        }
        return status_to_code.get(status, ErrorCode.INTERNAL_SERVER_ERROR.value)
    
    @staticmethod
    def _get_default_category(status: int) -> str:
        """Get default error category based on HTTP status."""
        status_to_category = {
            400: ErrorCategory.VALIDATION.value,
            401: ErrorCategory.AUTHENTICATION.value,
            403: ErrorCategory.AUTHORIZATION.value,
            404: ErrorCategory.BUSINESS_LOGIC.value,
            409: ErrorCategory.BUSINESS_LOGIC.value,
            422: ErrorCategory.BUSINESS_LOGIC.value,
            500: ErrorCategory.SYSTEM.value
        }
        return status_to_category.get(status, ErrorCategory.SYSTEM.value)
    
    @staticmethod
    def not_found(resource: str = 'Resource', error_code: Optional[str] = None) -> Tuple[Any, int]:
        """Standard not found response"""
        return ResponseService.error(
            message=f'{resource} not found',
            status=404,
            error_code=error_code or ErrorCode.RESOURCE_NOT_FOUND.value,
            category=ErrorCategory.BUSINESS_LOGIC
        )
    
    @staticmethod
    def validation_error(
        message: str, 
        field: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Tuple[Any, int]:
        """Validation error response"""
        return ResponseService.error(
            message=message,
            status=400,
            error_code=error_code or ErrorCode.INVALID_INPUT.value,
            category=ErrorCategory.VALIDATION,
            field=field,
            details=details
        )
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized', error_code: Optional[str] = None) -> Tuple[Any, int]:
        """Unauthorized response"""
        return ResponseService.error(
            message=message,
            status=401,
            error_code=error_code or ErrorCode.UNAUTHORIZED.value,
            category=ErrorCategory.AUTHENTICATION
        )
    
    @staticmethod
    def forbidden(message: str = 'Forbidden', error_code: Optional[str] = None) -> Tuple[Any, int]:
        """Forbidden response"""
        return ResponseService.error(
            message=message,
            status=403,
            error_code=error_code or ErrorCode.FORBIDDEN.value,
            category=ErrorCategory.AUTHORIZATION
        )
    
    @staticmethod
    def conflict(message: str, error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """Conflict response (409)"""
        return ResponseService.error(
            message=message,
            status=409,
            error_code=error_code or ErrorCode.RESOURCE_CONFLICT.value,
            category=ErrorCategory.BUSINESS_LOGIC,
            details=details
        )
    
    @staticmethod
    def business_error(message: str, error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """Business logic error response (422)"""
        return ResponseService.error(
            message=message,
            status=422,
            error_code=error_code or ErrorCode.BUSINESS_RULE_VIOLATION.value,
            category=ErrorCategory.BUSINESS_LOGIC,
            details=details
        )
    
    @staticmethod
    def server_error(message: str = 'Internal server error', error_code: Optional[str] = None, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """Server error response"""
        return ResponseService.error(
            message=message,
            status=500,
            error_code=error_code or ErrorCode.INTERNAL_SERVER_ERROR.value,
            category=ErrorCategory.SYSTEM,
            details=details
        )
    
    @staticmethod
    def file_operation_error(message: str, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """File operation error response"""
        return ResponseService.error(
            message=message,
            status=500,
            error_code=ErrorCode.FILE_OPERATION_ERROR.value,
            category=ErrorCategory.FILE_OPERATION,
            details=details
        )
    
    @staticmethod
    def database_error(message: str, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """Database error response"""
        return ResponseService.error(
            message=message,
            status=500,
            error_code=ErrorCode.DATABASE_ERROR.value,
            category=ErrorCategory.DATABASE,
            details=details
        )
