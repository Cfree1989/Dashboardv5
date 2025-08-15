import functools
from flask import request, jsonify, g
from app.services.auth_service import decode_token, get_token_from_request
import jwt

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Get token from cookies (preferred) or Authorization header (fallback)
        token = get_token_from_request(request)
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        try:
            payload = decode_token(token)
            g.workstation_id = payload.get('workstation_id')
            # Provide a safe default for admin routes that expect g.staff_name
            g.staff_name = payload.get('staff_name') or payload.get('workstation_id') or 'Admin'
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated