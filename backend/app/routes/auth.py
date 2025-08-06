from flask import Blueprint, request, jsonify, g
from app.services.auth_service import generate_token
from functools import wraps
from flask import current_app
from app.utils.decorators import token_required
from app import limiter

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# This is a temporary, insecure way to store credentials.
# In a real application, this would be configured securely.
WORKSTATIONS = {
    "front-desk": "password123"
}

@bp.route('/login', methods=['POST'])
@limiter.limit("10 per hour")
def login():
    data = request.get_json()
    if not data or not data.get('workstation_id') or not data.get('password'):
        return jsonify({"message": "Could not verify"}), 401

    workstation_id = data.get('workstation_id')
    password = data.get('password')

    if workstation_id in WORKSTATIONS and WORKSTATIONS[workstation_id] == password:
        token = generate_token(workstation_id)

        return jsonify({'token': token})

    return jsonify({"message": "Could not verify"}), 401

@bp.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'Protected endpoint', 'workstation_id': g.workstation_id})
