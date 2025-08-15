# type: ignore
import pytest
import os
from app.services.auth_service import generate_token, decode_token, set_auth_cookie, clear_auth_cookies, get_token_from_request
from app.utils.decorators import token_required
from flask import request, jsonify, g

def test_generate_token(app):
    """Test JWT token generation."""
    with app.app_context():
        token = generate_token('test-workstation')
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

def test_decode_token(app):
    """Test JWT token decoding."""
    with app.app_context():
        token = generate_token('test-workstation')
        payload = decode_token(token)
        assert payload['workstation_id'] == 'test-workstation'
        assert 'exp' in payload

def test_set_auth_cookie(app):
    """Test setting JWT token as httpOnly cookie."""
    with app.app_context():
        from flask import make_response
        token = generate_token('test-workstation')
        response = make_response(jsonify({'message': 'test'}))
        
        response = set_auth_cookie(response, token, 'test-workstation')
        
        # Check that both httpOnly and client cookies are set
        cookies = response.headers.getlist('Set-Cookie')
        assert len(cookies) == 2
        
        # Check httpOnly cookie
        httponly_cookie = [c for c in cookies if 'auth_token=' in c and 'HttpOnly' in c][0]
        assert 'auth_token=' in httponly_cookie
        assert 'HttpOnly' in httponly_cookie
        
        # Check client cookie
        client_cookie = [c for c in cookies if 'auth_token_client=' in c][0]
        assert 'auth_token_client=' in client_cookie
        assert 'HttpOnly' not in client_cookie

def test_clear_auth_cookies(app):
    """Test clearing JWT cookies."""
    with app.app_context():
        from flask import make_response
        response = make_response(jsonify({'message': 'test'}))
        
        response = clear_auth_cookies(response)
        
        # Check that both cookies are cleared
        cookies = response.headers.getlist('Set-Cookie')
        assert len(cookies) == 2
        
        # Both should have Max-Age=0 (expired)
        for cookie in cookies:
            assert 'Max-Age=0' in cookie

def test_get_token_from_request_cookie(app):
    """Test extracting token from cookie."""
    with app.app_context():
        token = generate_token('test-workstation')
        
        # Mock request with cookie
        with app.test_request_context('/', headers={'Cookie': f'auth_token={token}'}):
            extracted_token = get_token_from_request(request)
            assert extracted_token == token

def test_get_token_from_request_header_fallback(app):
    """Test extracting token from Authorization header as fallback."""
    with app.app_context():
        token = generate_token('test-workstation')
        
        # Mock request with Authorization header
        with app.test_request_context('/', headers={'Authorization': f'Bearer {token}'}):
            extracted_token = get_token_from_request(request)
            assert extracted_token == token

def test_get_token_from_request_missing(app):
    """Test handling when no token is present."""
    with app.app_context():
        # Mock request without token
        with app.test_request_context('/'):
            extracted_token = get_token_from_request(request)
            assert extracted_token is None

def test_login_sets_cookies(client):
    """Test that login endpoint sets JWT cookies."""
    response = client.post('/api/v1/auth/login', 
                          json={'workstation_id': 'front-desk', 'password': 'password123'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful'
    assert response.json['workstation_id'] == 'front-desk'
    
    # Check that cookies are set
    cookies = response.headers.getlist('Set-Cookie')
    assert len(cookies) == 2
    
    # Check httpOnly cookie
    httponly_cookie = [c for c in cookies if 'auth_token=' in c and 'HttpOnly' in c][0]
    assert 'auth_token=' in httponly_cookie
    assert 'HttpOnly' in httponly_cookie
    
    # Check client cookie
    client_cookie = [c for c in cookies if 'auth_token_client=' in c][0]
    assert 'auth_token_client=' in client_cookie

def test_logout_clears_cookies(client):
    """Test that logout endpoint clears JWT cookies."""
    response = client.post('/api/v1/auth/logout')
    
    assert response.status_code == 200
    assert response.json['message'] == 'Logout successful'
    
    # Check that cookies are cleared
    cookies = response.headers.getlist('Set-Cookie')
    assert len(cookies) == 2
    
    # Both should have Max-Age=0 (expired)
    for cookie in cookies:
        assert 'Max-Age=0' in cookie

def test_protected_endpoint_with_cookie(client):
    """Test accessing protected endpoint with JWT cookie."""
    # First login to get cookies
    login_response = client.post('/api/v1/auth/login', 
                                json={'workstation_id': 'front-desk', 'password': 'password123'})
    assert login_response.status_code == 200
    
    # Extract cookies from login response
    cookies = {}
    for cookie in login_response.headers.getlist('Set-Cookie'):
        if 'auth_token=' in cookie:
            # Parse cookie string to get name and value
            cookie_parts = cookie.split(';')[0].split('=')
            cookies[cookie_parts[0]] = cookie_parts[1]
    
    # Access protected endpoint with cookies
    response = client.get('/api/v1/auth/protected', headers={'Cookie': f"auth_token={cookies['auth_token']}"})
    
    assert response.status_code == 200
    assert response.json['message'] == 'Protected endpoint'
    assert response.json['workstation_id'] == 'front-desk'

def test_protected_endpoint_with_header_fallback(client):
    """Test accessing protected endpoint with Authorization header (fallback)."""
    # First login to get token
    login_response = client.post('/api/v1/auth/login', 
                                json={'workstation_id': 'front-desk', 'password': 'password123'})
    assert login_response.status_code == 200
    
    # Extract token from client cookie for header
    cookies = {}
    for cookie in login_response.headers.getlist('Set-Cookie'):
        if 'auth_token_client=' in cookie:
            cookie_parts = cookie.split(';')[0].split('=')
            cookies[cookie_parts[0]] = cookie_parts[1]
    
    token = cookies['auth_token_client']
    
    # Access protected endpoint with Authorization header
    response = client.get('/api/v1/auth/protected', 
                         headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'Protected endpoint'
    assert response.json['workstation_id'] == 'front-desk'

def test_protected_endpoint_no_token(client):
    """Test accessing protected endpoint without token."""
    response = client.get('/api/v1/auth/protected')
    
    assert response.status_code == 401
    assert response.json['message'] == 'Token is missing'

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/api/v1/auth/login', 
                          json={'workstation_id': 'invalid', 'password': 'wrong'})
    
    assert response.status_code == 401
    assert response.json['message'] == 'Could not verify'
    
    # Check that no cookies are set
    cookies = response.headers.getlist('Set-Cookie')
    assert len(cookies) == 0