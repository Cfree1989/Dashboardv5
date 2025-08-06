# type: ignore
import pytest

def test_login_success(client):
    resp = client.post(
        '/api/v1/auth/login', json={'workstation_id': 'front-desk', 'password': 'password123'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'token' in data

@pytest.mark.parametrize('password', ['wrong', '', None])
def test_login_failure(client, password):
    payload = {'workstation_id': 'front-desk'}
    if password is not None:
        payload['password'] = password
    resp = client.post('/api/v1/auth/login', json=payload)
    assert resp.status_code == 401


def test_protected_no_token(client):
    resp = client.get('/api/v1/auth/protected')
    assert resp.status_code == 401


def test_protected_with_token(client, token):
    resp = client.get(
        '/api/v1/auth/protected', headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['workstation_id'] == 'front-desk'