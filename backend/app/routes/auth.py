from flask import Blueprint, request, jsonify, g, make_response
from app.business_logic.shared_services import auth_service
from functools import wraps
from flask import current_app
from app.utils.decorators import token_required
from app import limiter
import os

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

def load_workstation_credentials():
    """Load workstation credentials from environment variables."""
    workstations = {}
    
    # Load development workstation credentials
    development_password = os.environ.get('WORKSTATION_DEVELOPMENT', 'password123')
    workstations['Development'] = development_password
    
    # Load workstation credentials
    for i in range(1, 4):  # Workstation 1, 2, 3
        workstation_id = f'Workstation {i}'
        password = os.environ.get(f'WORKSTATION_{i}', 'Fabrication')
        workstations[workstation_id] = password
    
    return workstations

# Load workstation credentials from environment variables
WORKSTATIONS = load_workstation_credentials()

@bp.route('/login', methods=['POST'])
@limiter.exempt
def login():
    data = request.get_json()
    if not data or not data.get('workstation_id') or not data.get('password'):
        return jsonify({"message": "Could not verify"}), 401

    workstation_id = data.get('workstation_id')
    password = data.get('password')

    if workstation_id in WORKSTATIONS and WORKSTATIONS[workstation_id] == password:
        token = auth_service.generate_token(workstation_id)
        
        # Create response with success message
        response = make_response(jsonify({
            'message': 'Login successful',
            'workstation_id': workstation_id,
            'token': token
        }))
        
        # Set JWT token as httpOnly cookie
        response = auth_service.set_auth_cookie(response, token, workstation_id)
        
        return response

    return jsonify({"message": "Could not verify"}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    """Logout by clearing JWT cookies."""
    response = make_response(jsonify({'message': 'Logout successful'}))
    response = auth_service.clear_auth_cookies(response)
    return response

@bp.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'Protected endpoint', 'workstation_id': g.workstation_id})
