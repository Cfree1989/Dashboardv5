# type: ignore
import pytest
from app import db
from app.models.job import Job


def create_job(app):
    with app.app_context():
        job = Job(
            student_name='Alice', student_email='alice@example.com', discipline='Art',
            class_number='101', original_filename='file.stl', display_name='file.stl',
            file_path='path', metadata_path='meta', printer='Prusa', color='Red', material='Filament'
        )
        db.session.add(job)
        db.session.commit()
        return job


def test_list_jobs_empty(client, token):
    resp = client.get('/api/v1/jobs', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_get_job_not_found(client, token):
    resp = client.get('/api/v1/jobs/nonexistent', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 404


def test_job_crud(client, token, app):
    job = create_job(app)
    job_id = job.id

    # Retrieve job
    resp = client.get(f'/api/v1/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['id'] == job_id

    # List jobs with filter
    resp = client.get(f'/api/v1/jobs?status=UPLOADED', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert any(item['id'] == job_id for item in resp.get_json())

    # Delete job in UPLOADED status
    resp = client.delete(f'/api/v1/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 204

    # Delete again -> 404
    resp = client.delete(f'/api/v1/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 404

    # Create job in non-deletable status
    with app.app_context():
        job2 = Job(
            student_name='Bob', student_email='bob@example.com', discipline='Eng',
            class_number='202', original_filename='file2.stl', display_name='file2.stl',
            file_path='path2', metadata_path='meta2', printer='Prusa', color='Blue', material='Resin',
            status='COMPLETED'
        )
        db.session.add(job2)
        db.session.commit()
        id2 = job2.id
    resp = client.delete(f'/api/v1/jobs/{id2}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 403


def test_approve_job_with_attribution_and_cost(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'Jane Doe'}, headers={'Authorization': f'Bearer {token}'})

    payload = {
        'staff_name': 'Jane Doe',
        'weight_g': 50,
        'time_hours': 2.5
    }
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'PENDING'
    assert data['last_updated_by'] == 'Jane Doe'
    assert data['weight_g'] == 50.0
    assert data['time_hours'] == 2.5
    # Filament at $0.10/g => $5.00, above $3 minimum
    assert data['cost_usd'] == 5.0


def test_approve_requires_active_staff_and_valid_numbers(client, token, app):
    job = create_job(app)
    # No staff added yet
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Ghost', 'weight_g': 10, 'time_hours': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Add inactive staff
    client.post('/api/v1/staff', json={'name': 'Inactive'}, headers={'Authorization': f'Bearer {token}'})
    client.patch('/api/v1/staff/Inactive', json={'is_active': False}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Inactive', 'weight_g': 10, 'time_hours': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Add active staff, but invalid numbers
    client.post('/api/v1/staff', json={'name': 'Active'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Active', 'weight_g': 0, 'time_hours': -1},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400


def test_approve_cost_minimum_applied_for_small_weight(client, token, app):
    job = create_job(app)
    # Force material to Resin for pricing difference, but ensure minimum applies
    with app.app_context():
        job.material = 'Resin'
        db.session.commit()
    client.post('/api/v1/staff', json={'name': 'Jane'}, headers={'Authorization': f'Bearer {token}'})

    # Small weight -> cost below $3, expect minimum $3.00
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Jane', 'weight_g': 5, 'time_hours': 0.5},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['cost_usd'] == 3.0


def test_review_toggle_persists_and_logs_event(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'Reviewer'}, headers={'Authorization': f'Bearer {token}'})

    # Initially unreviewed
    resp = client.get(f'/api/v1/jobs/{job.id}', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.get_json().get('staff_viewed_at') is None

    # Mark reviewed
    resp = client.post(
        f'/api/v1/jobs/{job.id}/review',
        json={'reviewed': True, 'staff_name': 'Reviewer'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['staff_viewed_at'] is not None

    # Clear (reapply NEW)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/review',
        json={'reviewed': False, 'staff_name': 'Reviewer'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['staff_viewed_at'] is None

    # Verify events include JobReviewed and JobReviewCleared
    resp_events = client.get(
        f'/api/v1/jobs/{job.id}/events',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_events.status_code == 200
    events = [e['event_type'] for e in resp_events.get_json()]
    assert 'JobReviewed' in events
    assert 'JobReviewCleared' in events


def test_review_status_guard(client, token, app):
    job = create_job(app)
    # Move job to non-UPLOADED status
    with app.app_context():
        j = Job.query.get(job.id)
        j.status = 'PENDING'
        db.session.commit()
    client.post('/api/v1/staff', json={'name': 'Reviewer'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post(
        f'/api/v1/jobs/{job.id}/review',
        json={'reviewed': True, 'staff_name': 'Reviewer'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400


def test_candidate_files_stub_returns_original_filename(client, token, app):
    job = create_job(app)
    resp = client.get(
        f'/api/v1/jobs/{job.id}/candidate-files',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'files' in data
    assert job.original_filename in data['files']


def test_reject_job_with_reasons(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'Reviewer'}, headers={'Authorization': f'Bearer {token}'})

    payload = {
        'staff_name': 'Reviewer',
        'reasons': ['Poor model quality'],
        'custom_reason': 'Walls too thin'
    }
    resp = client.post(
        f'/api/v1/jobs/{job.id}/reject',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'REJECTED'
    assert 'reject_reasons' in data
    assert any('Poor model quality' in r for r in data['reject_reasons'])
    assert any('Walls too thin' in r for r in data['reject_reasons'])

    # Events include StaffRejected
    resp_events = client.get(
        f'/api/v1/jobs/{job.id}/events',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_events.status_code == 200
    events = [e['event_type'] for e in resp_events.get_json()]
    assert 'StaffRejected' in events


def test_status_transitions_printing_complete_picked_up(client, token, app):
    job = create_job(app)
    # Move to READYTOPRINT via confirm path shortcut
    with app.app_context():
        j = Job.query.get(job.id)
        j.status = 'READYTOPRINT'
        db.session.commit()
    client.post('/api/v1/staff', json={'name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})

    # mark printing
    resp = client.post(
        f'/api/v1/jobs/{job.id}/mark-printing',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'PRINTING'

    # mark complete (requires PRINTING)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/mark-complete',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'COMPLETED'

    # mark picked up (requires COMPLETED)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/mark-picked-up',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'PAIDPICKEDUP'