# type: ignore
import os
import sys
import pytest

# Ensure 'backend' (which contains the 'app' package) is importable
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app import create_app, db


@pytest.fixture
def app():
    # Configure in-memory database for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    test_app = create_app()
    test_app.config['TESTING'] = True
    with test_app.app_context():
        db.create_all()
    yield test_app
    # Teardown database
    with test_app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def token(client):
    # Login to obtain JWT
    resp = client.post(
        '/api/v1/auth/login', json={'workstation_id': 'Development', 'password': 'password123'}
    )
    data = resp.get_json()
    return data['token']


@pytest.fixture(autouse=True)
def app_ctx(app):
    """Automatically push an application context for tests"""
    with app.app_context():
        yield


@pytest.fixture
def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


