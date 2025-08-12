# type: ignore
import io
import pytest


def test_analytics_events_requires_auth(client):
    # Should reject unauthorized requests
    resp = client.get('/api/v1/analytics/events')
    assert resp.status_code == 401


def test_analytics_events_list(client, token):
    # Submit a job to generate a JobCreated event
    data = {
        'student_name': 'Zoe',
        'student_email': 'zoe@example.com',
        'discipline': 'Design',
        'class_number': '505',
        'printer': 'Prusa',
        'color': 'Black',
        'material': 'Filament',
        'file': (io.BytesIO(b'model content'), 'test.stl')
    }
    submit_resp = client.post(
        '/api/v1/submit', data=data, content_type='multipart/form-data'
    )
    assert submit_resp.status_code == 201
    job = submit_resp.get_json()
    job_id = job['id']

    # Retrieve all events via analytics endpoint
    resp = client.get(
        '/api/v1/analytics/events',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    events = resp.get_json()
    # Ensure at least one JobCreated event for the submitted job
    assert any(
        evt['event_type'] == 'JobCreated' and evt['job_id'] == job_id
        for evt in events
    )


def test_no_sqlite_fallback_guard_in_non_test_env(monkeypatch):
    # Simulate production-like env: no TESTING flag and no DATABASE_URL env var
    monkeypatch.delenv('DATABASE_URL', raising=False)
    import app as app_pkg
    # Create app should raise since DATABASE_URL is missing and not TESTING
    try:
        app_pkg.create_app()
        raised = False
    except RuntimeError as e:
        raised = 'DATABASE_URL is not set' in str(e)
    assert raised