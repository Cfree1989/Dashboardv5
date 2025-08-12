# type: ignore
import io
import os
import time
import pytest


def create_submission(client, name='Alice', email='alice@example.com'):
    data = {
        'student_name': name,
        'student_email': email,
        'discipline': 'Eng',
        'class_number': '101',
        'printer': 'Prusa',
        'color': 'Blue',
        'material': 'Filament',
        'file': (io.BytesIO(b'solid data'), 'model.stl'),
    }
    resp = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
    assert resp.status_code == 201
    return resp.get_json()


def test_resend_confirmation_happy_path(client):
    job = create_submission(client)

    # Call resend using job_id
    resp = client.post('/api/v1/submit/resend-confirmation', json={'job_id': job['id']})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['job_id'] == job['id']


def test_resend_confirmation_invalid_token(client):
    resp = client.post('/api/v1/submit/resend-confirmation', json={'token': 'not-a-real-token'})
    assert resp.status_code == 400


def test_resend_confirmation_missing_params(client):
    resp = client.post('/api/v1/submit/resend-confirmation', json={})
    assert resp.status_code == 400


def test_resend_confirmation_job_not_found(client):
    # Unknown job_id
    resp = client.post('/api/v1/submit/resend-confirmation', json={'job_id': 'nonexistent'})
    assert resp.status_code == 404


def test_resend_confirmation_already_confirmed(client, app):
    job = create_submission(client, name='Bob', email='bob@example.com')

    # Mark job confirmed by calling confirm endpoint using a fresh token
    from app.services.token_service import generate_confirmation_token
    with app.app_context():
        token = generate_confirmation_token(job['id'])
    ok = client.post(f'/api/v1/submit/confirm/{token}')
    assert ok.status_code == 200

    # Resend should now be rejected
    resp = client.post('/api/v1/submit/resend-confirmation', json={'job_id': job['id']})
    assert resp.status_code == 400


def test_resend_confirmation_rate_limit(client):
    job = create_submission(client, name='Carol', email='carol@example.com')

    # First resend OK
    r1 = client.post('/api/v1/submit/resend-confirmation', json={'job_id': job['id']})
    assert r1.status_code == 200

    # Second within the same hour should 429
    r2 = client.post('/api/v1/submit/resend-confirmation', json={'job_id': job['id']})
    assert r2.status_code == 429
