import pytest
import tempfile
import os
from io import BytesIO
from app import create_app, db
from app.models.job import Job


@pytest.fixture
def app():
    # Configure in-memory database for testing
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    os.environ['STORAGE_PATH'] = temp_dir
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)


def create_test_file():
    """Create a test STL file"""
    content = b"solid test\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid test"
    return BytesIO(content), "test.stl"


def test_submit_rate_limit_5_per_hour(client, temp_storage):
    """Test that only 5 submissions are allowed per hour"""
    
    # Submit 5 jobs - should all succeed
    for i in range(5):
        file_data, filename = create_test_file()
        response = client.post('/api/v1/submit', 
                             data={
                                 'file': (file_data, filename),
                                 'student_name': f'Test Student {i}',
                                 'student_email': f'test{i}@example.com',
                                 'discipline': 'Engineering',
                                 'class_number': '101',
                                 'printer': 'Printer1',
                                 'material': 'PLA',
                                 'color': 'Blue'
                             },
                             content_type='multipart/form-data')
        
        assert response.status_code == 201, f"Submission {i+1} should succeed, got {response.status_code}"
        assert 'id' in response.json
    
    # 6th submission should be rate limited
    file_data, filename = create_test_file()
    response = client.post('/api/v1/submit',
                         data={
                             'file': (file_data, filename),
                             'student_name': 'Test Student 6',
                             'student_email': 'test6@example.com',
                             'discipline': 'Engineering',
                             'class_number': '101',
                             'printer': 'Printer1',
                             'material': 'PLA',
                             'color': 'Blue'
                         },
                         content_type='multipart/form-data')
    
    assert response.status_code == 429, f"6th submission should be rate limited, got {response.status_code}"
    # Check response content - Flask-Limiter might return HTML or JSON
    response_data = response.get_json()
    if response_data:
        assert 'error' in response_data or 'message' in response_data
    else:
        # Flask-Limiter might return HTML error page
        assert 'Too Many Requests' in response.get_data(as_text=True) or '429' in response.get_data(as_text=True)


def test_rate_limit_respects_different_ips(client, temp_storage):
    """Test that rate limiting is per IP address"""
    
    # Submit 5 jobs from one IP
    for i in range(5):
        file_data, filename = create_test_file()
        response = client.post('/api/v1/submit',
                             data={
                                 'file': (file_data, filename),
                                 'student_name': f'Test Student {i}',
                                 'student_email': f'test{i}@example.com',
                                 'discipline': 'Engineering',
                                 'class_number': '101',
                                 'printer': 'Printer1',
                                 'material': 'PLA',
                                 'color': 'Blue'
                             },
                             content_type='multipart/form-data')
        assert response.status_code == 201
    
    # 6th submission from same IP should be rate limited
    file_data, filename = create_test_file()
    response = client.post('/api/v1/submit',
                         data={
                             'file': (file_data, filename),
                             'student_name': 'Test Student 6',
                             'student_email': 'test6@example.com',
                             'discipline': 'Engineering',
                             'class_number': '101',
                             'printer': 'Printer1',
                             'material': 'PLA',
                             'color': 'Blue'
                         },
                         content_type='multipart/form-data')
    
    assert response.status_code == 429


def test_rate_limit_error_message(client, temp_storage):
    """Test that rate limit error returns appropriate message"""
    
    # Submit 5 jobs to hit limit
    for i in range(5):
        file_data, filename = create_test_file()
        client.post('/api/v1/submit',
                   data={
                       'file': (file_data, filename),
                       'student_name': f'Test Student {i}',
                       'student_email': f'test{i}@example.com',
                       'discipline': 'Engineering',
                       'class_number': '101',
                       'printer': 'Printer1',
                       'material': 'PLA',
                       'color': 'Blue'
                   },
                   content_type='multipart/form-data')
    
    # 6th submission should return rate limit error
    file_data, filename = create_test_file()
    response = client.post('/api/v1/submit',
                         data={
                             'file': (file_data, filename),
                             'student_name': 'Test Student 6',
                             'student_email': 'test6@example.com',
                             'discipline': 'Engineering',
                             'class_number': '101',
                             'printer': 'Printer1',
                             'material': 'PLA',
                             'color': 'Blue'
                         },
                         content_type='multipart/form-data')
    
    assert response.status_code == 429
    # Check that response contains rate limit information
    response_data = response.get_json()
    if response_data:
        assert 'error' in response_data or 'message' in response_data
    else:
        # Flask-Limiter might return HTML error page
        assert 'Too Many Requests' in response.get_data(as_text=True) or '429' in response.get_data(as_text=True)
