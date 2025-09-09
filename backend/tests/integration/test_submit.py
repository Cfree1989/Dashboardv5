# type: ignore
import pytest
import io


def test_submit_job_success(client):
    data = {
        'student_name': 'Charlie',
        'student_email': 'charlie@example.com',
        'discipline': 'Eng',
        'class_number': '303',
        'print_method': 'Filament',
        'printer': 'Prusa MK4S',
        'color': 'True Black',
        'material': 'PLA',
        'file': (io.BytesIO(b'solid data'), 'model.stl')
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    if resp.status_code != 201:
        print(f"Response: {resp.get_json()}")
    assert resp.status_code == 201
    json_data = resp.get_json()
    assert json_data['student_name'] == 'Charlie'
    assert 'short_id' in json_data and isinstance(json_data['short_id'], str) and 6 <= len(json_data['short_id']) <= 12


def test_submit_missing_file(client):
    data = {'student_name': 'Dana'}
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_submit_bad_extension(client):
    data = {
        'student_name': 'Eve',
        'file': (io.BytesIO(b'data'), 'model.txt')
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_submit_duplicate(client):
    data = {
        'student_name': 'Frank',
        'student_email': 'frank@example.com',
        'discipline': 'Art',
        'class_number': '404',
        'print_method': 'Filament',
        'printer': 'Prusa MK4S',
        'color': 'Red',
        'material': 'PLA',
        'file': (io.BytesIO(b'dupe data'), 'dup.stl')
    }
    resp1 = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp1.status_code == 201
    data['file'] = (io.BytesIO(b'dupe data'), 'dup.stl')
    resp2 = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp2.status_code == 409

# type: ignore
import pytest
import io


def test_submit_job_success(client):
    data = {
        'student_name': 'Charlie',
        'student_email': 'charlie@example.com',
        'discipline': 'Eng',
        'class_number': '303',
        'print_method': 'Filament',
        'printer': 'Prusa MK4S',
        'color': 'True Black',
        'material': 'PLA',
        'file': (io.BytesIO(b'solid data'), 'model.stl')
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    if resp.status_code != 201:
        print(f"Response: {resp.get_json()}")
    assert resp.status_code == 201
    json = resp.get_json()
    assert json['student_name'] == 'Charlie'
    # short_id should exist and be short
    assert 'short_id' in json and isinstance(json['short_id'], str) and 6 <= len(json['short_id']) <= 12


def test_submit_missing_file(client):
    data = {
        'student_name': 'Dana'
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_submit_bad_extension(client):
    data = {
        'student_name': 'Eve',
        'file': (io.BytesIO(b'data'), 'model.txt')
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_submit_duplicate(client):
    # First submission
    data = {
        'student_name': 'Frank',
        'student_email': 'frank@example.com',
        'discipline': 'Art',
        'class_number': '404',
        'print_method': 'Filament',
        'printer': 'Prusa MK4S',
        'color': 'Red',
        'material': 'PLA',
        'file': (io.BytesIO(b'dupe data'), 'dup.stl')
    }
    resp1 = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp1.status_code == 201
    # Duplicate submission - recreate file stream to avoid closed file
    data['file'] = (io.BytesIO(b'dupe data'), 'dup.stl')
    resp2 = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp2.status_code == 409