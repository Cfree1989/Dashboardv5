import pytest
from app import db
from app.models.job import Job


def seed_job():
    job = Job(
        student_name='Test',
        student_email='test@example.com',
        discipline='Eng',
        class_number='101',
        original_filename='model.stl',
        display_name='model.stl',
        file_path='path',
        metadata_path='meta',
        printer='Prusa XL',
        color='True Black',
        material='PLA'
    )
    db.session.add(job)
    db.session.commit()
    return job


def test_validate_job_success(client, token):
    job = seed_job()
    resp = client.get(
        f'/api/v1/jobs/{job.id}/validate',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['message'] == 'Job is valid'
    assert data['job_id'] == str(job.id)


def test_validate_job_not_found(client, token):
    resp = client.get(
        '/api/v1/jobs/nonexistent_id/validate',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 404
    data = resp.get_json()
    assert 'message' in data
