import datetime
import jwt
from flask import current_app

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