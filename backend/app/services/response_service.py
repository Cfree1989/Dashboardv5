# backend/app/services/response_service.py
from flask import jsonify
from typing import Any, Dict, Optional, Tuple
import json

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
    def error(message: str, status: int = 400, details: Optional[Dict] = None) -> Tuple[Any, int]:
        """Standard error response - returns tuple for Flask compatibility"""
        response_data = {'message': message}
        if details:
            response_data.update(details)
        return ResponseService._safe_jsonify(response_data), status
    
    @staticmethod
    def not_found(resource: str = 'Resource') -> Tuple[Any, int]:
        """Standard not found response"""
        return ResponseService._safe_jsonify({'message': f'{resource} not found'}), 404
    
    @staticmethod
    def validation_error(message: str, field: Optional[str] = None) -> Tuple[Any, int]:
        """Validation error response"""
        data = {'message': message}
        if field:
            data['field'] = field
        return ResponseService._safe_jsonify(data), 400
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> Tuple[Any, int]:
        """Unauthorized response"""
        return ResponseService._safe_jsonify({'message': message}), 401
    
    @staticmethod
    def forbidden(message: str = 'Forbidden') -> Tuple[Any, int]:
        """Forbidden response"""
        return ResponseService._safe_jsonify({'message': message}), 403
    
    @staticmethod
    def server_error(message: str = 'Internal server error') -> Tuple[Any, int]:
        """Server error response"""
        return ResponseService._safe_jsonify({'message': message}), 500
