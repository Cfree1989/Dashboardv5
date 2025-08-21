import datetime
import jwt
from flask import current_app, make_response

def generate_token(workstation_id, expires_in=43200):
    """Generate a JWT token for a workstation with expiration in seconds."""
    payload = {
        'workstation_id': workstation_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    """Decode a JWT token and return its payload or raise an exception if invalid."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        raise
    except jwt.InvalidTokenError:
        # Token is invalid
        raise

def set_auth_cookie(response, token, workstation_id):
    """Set JWT token as an httpOnly cookie on the response."""
    cookie_name = current_app.config['JWT_COOKIE_NAME']
    max_age = current_app.config['JWT_COOKIE_MAX_AGE']
    secure = current_app.config['JWT_COOKIE_SECURE']
    httponly = current_app.config['JWT_COOKIE_HTTPONLY']
    samesite = current_app.config['JWT_COOKIE_SAMESITE']
    domain = current_app.config['JWT_COOKIE_DOMAIN']
    path = current_app.config['JWT_COOKIE_PATH']
    
    response.set_cookie(
        cookie_name,
        token,
        max_age=max_age,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
        domain=domain,
        path=path
    )
    
    return response

def clear_auth_cookies(response):
    """Clear all JWT cookies from the response."""
    cookie_name = current_app.config['JWT_COOKIE_NAME']
    domain = current_app.config['JWT_COOKIE_DOMAIN']
    path = current_app.config['JWT_COOKIE_PATH']
    
    # Clear httpOnly cookie
    response.delete_cookie(
        cookie_name,
        domain=domain,
        path=path
    )
    
    return response

def get_token_from_request(request):
    """Extract JWT token from request cookies or Authorization header (fallback)."""
    cookie_name = current_app.config['JWT_COOKIE_NAME']
    
    # First try to get token from httpOnly cookie
    token = request.cookies.get(cookie_name)
    
    # Fallback to Authorization header for backward compatibility
    if not token:
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]
    
    return token