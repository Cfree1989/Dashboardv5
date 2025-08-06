# type: ignore
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
import pytest
from app import create_app, db

@pytest.fixture
def app():
    # Configure in-memory database for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
    yield app
    # Teardown database
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def token(client):
    # Login to obtain JWT
    resp = client.post(
        '/api/v1/auth/login', json={'workstation_id': 'front-desk', 'password': 'password123'}
    )
    data = resp.get_json()
    return data['token']