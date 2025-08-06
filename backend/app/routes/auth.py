from flask import Blueprint, request, jsonify
import jwt
import datetime
from functools import wraps
from flask import current_app

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# This is a temporary, insecure way to store credentials.
# In a real application, this would be configured securely.
WORKSTATIONS = {
    "front-desk": "password123"
}

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('workstation_id') or not data.get('password'):
        return jsonify({"message": "Could not verify"}), 401

    workstation_id = data.get('workstation_id')
    password = data.get('password')

    if workstation_id in WORKSTATIONS and WORKSTATIONS[workstation_id] == password:
        token = jwt.encode({
            'workstation_id': workstation_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'token': token})

    return jsonify({"message": "Could not verify"}), 401
