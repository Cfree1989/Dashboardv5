import functools
from flask import request, jsonify, g
from app.services.auth_service import decode_token
import jwt

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Token is missing'}), 401
        token = auth_header.split('Bearer ')[1]
        try:
            payload = decode_token(token)
            g.workstation_id = payload.get('workstation_id')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated