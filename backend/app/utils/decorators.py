import functools
from flask import request, jsonify, g
from app.business_logic.shared_services import auth_service
from app.business_logic.shared_services.response_service import ResponseService, ErrorCode
import jwt

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Get token from cookies (preferred) or Authorization header (fallback)
        token = auth_service.get_token_from_request(request)
        
        if not token:
            return ResponseService.unauthorized(
                message="Token is missing",
                error_code=ErrorCode.UNAUTHORIZED.value
            )
            
        try:
            payload = auth_service.decode_token(token)
            g.workstation_id = payload.get('workstation_id')
            # Provide a safe default for admin routes that expect g.staff_name
            g.staff_name = payload.get('staff_name') or payload.get('workstation_id') or 'Admin'
        except jwt.ExpiredSignatureError:
            return ResponseService.unauthorized(
                message="Token has expired",
                error_code=ErrorCode.TOKEN_EXPIRED.value
            )
        except jwt.InvalidTokenError:
            return ResponseService.unauthorized(
                message="Invalid token",
                error_code=ErrorCode.INVALID_TOKEN.value
            )
        return f(*args, **kwargs)
    return decorated