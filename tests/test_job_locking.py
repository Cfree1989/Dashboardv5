# type: ignore
import pytest
import time
from app.models.job import Job
from app import db
from app.services.auth_service import generate_token
from datetime import datetime, timedelta

@pytest.fixture
def job(app):
    # Create a job record for locking tests
    with app.app_context():
        job = Job(
            student_name="Test Student",
            student_email="test@example.com",
            discipline="Test",
            class_number="001",
            original_filename="file.stl",
            display_name="Test File",
            file_path="storage/file.stl",
            metadata_path="storage/file.json",
            printer="Printer1",
            color="Blue",
            material="PLA"
        )
        db.session.add(job)
        db.session.commit()
        return job


def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


def test_lock_unlock_extend(client, token, job):
    # Lock the job
    resp = client.post(f'/api/v1/jobs/{job.id}/lock', headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['locked_by'] == 'Development'
    assert data['locked_until'] is not None

    # Trying to lock again immediately should conflict
    resp_conflict = client.post(f'/api/v1/jobs/{job.id}/lock', headers=auth_headers(token))
    assert resp_conflict.status_code == 409

    # Extend the lock
    resp_ext = client.post(f'/api/v1/jobs/{job.id}/extend', headers=auth_headers(token))
    assert resp_ext.status_code == 200
    data_ext = resp_ext.get_json()
    assert data_ext['locked_by'] == 'Development'

    # Unlock the job
    resp_un = client.post(f'/api/v1/jobs/{job.id}/unlock', headers=auth_headers(token))
    assert resp_un.status_code == 200
    data_un = resp_un.get_json()
    assert data_un['locked_by'] is None
    assert data_un['locked_until'] is None


def test_lock_conflict_between_users(client, token, job, app):
    # First user locks
    resp1 = client.post(f'/api/v1/jobs/{job.id}/lock', headers=auth_headers(token))
    assert resp1.status_code == 200

    # Another user tries to lock
    with app.app_context():
        other_token = generate_token('OtherUser')
    resp2 = client.post(f'/api/v1/jobs/{job.id}/lock', headers=auth_headers(other_token))
    assert resp2.status_code == 409

    # Owner unlocks
    resp_un = client.post(f'/api/v1/jobs/{job.id}/unlock', headers=auth_headers(token))
    assert resp_un.status_code == 200
    data_un = resp_un.get_json()
    assert data_un['locked_by'] is None
    assert data_un['locked_until'] is None
