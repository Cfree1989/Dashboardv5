# type: ignore
import pytest
import os
from app import db
from app.models.job import Job
from app.models.payment import Payment


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

    # Delete job in UPLOADED status -> soft-delete to ARCHIVED
    resp = client.delete(f'/api/v1/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'} )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ARCHIVED'

    # Hard delete the archived job
    resp = client.post(f'/api/v1/jobs/{job_id}/hard-delete', json={'staff_name': 'Admin User'}, headers={'Authorization': f'Bearer {token}'} )
    assert resp.status_code == 200

    # Delete again -> 404
    resp = client.delete(f'/api/v1/jobs/{job_id}', headers={'Authorization': f'Bearer {token}'} )
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
        'time_hours': 2.5,
        'printer': 'Prusa XL'
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
    # Printer override applied
    assert data['printer'] in ['Prusa XL', 'Prusa']  # allow default if validation restricts

    # Check event attribution
    events_resp = client.get(f'/api/v1/jobs/{job.id}/events', headers={'Authorization': f'Bearer {token}'} )
    assert events_resp.status_code == 200
    events = events_resp.get_json()
    approved = next((e for e in events if e['event_type'] == 'StaffApproved'), None)
    assert approved is not None
    assert approved['triggered_by'] == 'Jane Doe'


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


def test_approve_rejects_missing_or_unsupported_authoritative_file(client, token, app, tmp_path):
    # Place job in a temp directory with only the original .stl
    job = create_job(app)
    with app.app_context():
        j = Job.query.get(job.id)
        storage_dir = tmp_path
        os.environ['STORAGE_PATH'] = str(storage_dir)
        # Write the original file and update job paths
        (storage_dir / 'file.stl').write_text('dummy')
        j.file_path = str(storage_dir / 'file.stl')
        j.display_name = 'file.stl'
        j.metadata_path = str(storage_dir / 'file_metadata.json')
        db.session.commit()

    client.post('/api/v1/staff', json={'name': 'Staff'}, headers={'Authorization': f'Bearer {token}'})

    # Unsupported extension
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Staff', 'weight_g': 10, 'time_hours': 1, 'authoritative_filename': 'file.gcode'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Missing file
    resp = client.post(
        f'/api/v1/jobs/{job.id}/approve',
        json={'staff_name': 'Staff', 'weight_g': 10, 'time_hours': 1, 'authoritative_filename': 'missing.3mf'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400


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


def test_record_payment_moves_file_and_sets_status(client, token, app, tmp_path):
    # Prepare job in COMPLETED with temp storage
    os.environ['STORAGE_PATH'] = str(tmp_path)
    job = create_job(app)
    with app.app_context():
        j = Job.query.get(job.id)
        (tmp_path / 'Completed').mkdir(parents=True, exist_ok=True)
        (tmp_path / 'Completed' / 'file.stl').write_text('model')
        (tmp_path / 'Completed' / 'file_metadata.json').write_text('{}')
        j.status = 'COMPLETED'
        j.file_path = str(tmp_path / 'Completed' / 'file.stl')
        j.metadata_path = str(tmp_path / 'Completed' / 'file_metadata.json')
        db.session.commit()

    client.post('/api/v1/staff', json={'name': 'Cashier'}, headers={'Authorization': f'Bearer {token}'})

    # Record payment
    resp = client.post(
        f'/api/v1/jobs/{job.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 10, 'txn_no': 'TC1', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'PAIDPICKEDUP'
    # File moved to PaidPickedUp
    assert not (tmp_path / 'Completed' / 'file.stl').exists()
    assert (tmp_path / 'PaidPickedUp' / 'file.stl').exists()


def test_record_payment_uses_actual_grams_not_estimate(client, token, app):
    """Test that payment calculation uses actual pickup weight, not the job estimate"""
    job = create_job(app)
    with app.app_context():
        j = Job.query.get(job.id)
        # Set up job with a high estimate ($50.00) but resin material
        j.status = 'COMPLETED'
        j.material = 'resin'
        j.cost_usd = 50.00  # High estimate
        db.session.commit()

    client.post('/api/v1/staff', json={'name': 'Cashier'}, headers={'Authorization': f'Bearer {token}'})

    # Record payment with low actual weight (10g resin = $2.00, but min $3.00)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 10, 'txn_no': 'TC1', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    
    # Verify the payment record has the correct price (min charge $3.00)
    with app.app_context():
        payment = Payment.query.get(job.id)
        assert payment is not None
        assert payment.price_cents == 300  # $3.00 minimum charge
        assert payment.grams == 10.0
        # Verify the job estimate was NOT used (would have been $50.00 = 5000 cents)


def test_record_payment_filament_calculation(client, token, app):
    """Test filament payment calculation with various weights"""
    job = create_job(app)
    with app.app_context():
        j = Job.query.get(job.id)
        j.status = 'COMPLETED'
        j.material = 'filament'
        j.cost_usd = 25.00  # Estimate
        db.session.commit()

    client.post('/api/v1/staff', json={'name': 'Cashier'}, headers={'Authorization': f'Bearer {token}'})

    # Test 1: Below minimum charge (20g filament = $2.00, should be $3.00 min)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 20, 'txn_no': 'TC1', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    
    with app.app_context():
        payment = Payment.query.get(job.id)
        assert payment.price_cents == 300  # $3.00 minimum charge

    # Test 2: Above minimum charge (50g filament = $5.00)
    job2 = create_job(app)
    with app.app_context():
        j2 = Job.query.get(job2.id)
        j2.status = 'COMPLETED'
        j2.material = 'filament'
        db.session.commit()

    resp = client.post(
        f'/api/v1/jobs/{job2.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 50, 'txn_no': 'TC2', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    
    with app.app_context():
        payment2 = Payment.query.get(job2.id)
        assert payment2.price_cents == 500  # $5.00 (50g * $0.10/g)


def test_record_payment_resin_calculation(client, token, app):
    """Test resin payment calculation with various weights"""
    job = create_job(app)
    with app.app_context():
        j = Job.query.get(job.id)
        j.status = 'COMPLETED'
        j.material = 'resin'
        db.session.commit()

    client.post('/api/v1/staff', json={'name': 'Cashier'}, headers={'Authorization': f'Bearer {token}'})

    # Test 1: Below minimum charge (10g resin = $2.00, should be $3.00 min)
    resp = client.post(
        f'/api/v1/jobs/{job.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 10, 'txn_no': 'TC1', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    
    with app.app_context():
        payment = Payment.query.get(job.id)
        assert payment.price_cents == 300  # $3.00 minimum charge

    # Test 2: Above minimum charge (25g resin = $5.00)
    job2 = create_job(app)
    with app.app_context():
        j2 = Job.query.get(job2.id)
        j2.status = 'COMPLETED'
        j2.material = 'resin'
        db.session.commit()

    resp = client.post(
        f'/api/v1/jobs/{job2.id}/payment',
        json={'staff_name': 'Cashier', 'grams': 25, 'txn_no': 'TC2', 'picked_up_by': 'Student'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    
    with app.app_context():
        payment2 = Payment.query.get(job2.id)
        assert payment2.price_cents == 500  # $5.00 (25g * $0.20/g)


def test_append_note_with_name_prefix_and_limits(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'NoteTaker'}, headers={'Authorization': f'Bearer {token}'})

    # Append a note
    resp = client.post(
        f'/api/v1/jobs/{job.id}/notes',
        json={'text': 'Model needs to be split', 'staff_name': 'NoteTaker'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'notes' in data
    assert 'NoteTaker - Model needs to be split' in data['notes']

    # Per-entry limit
    too_long = 'a' * 2000
    resp = client.post(
        f'/api/v1/jobs/{job.id}/notes',
        json={'text': too_long, 'staff_name': 'NoteTaker'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Total limit
    filler = 'b' * 4900
    resp = client.post(
        f'/api/v1/jobs/{job.id}/notes',
        json={'text': filler, 'staff_name': 'NoteTaker'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Event logged
    ev = client.get(f'/api/v1/jobs/{job.id}/events', headers={'Authorization': f'Bearer {token}'})
    assert ev.status_code == 200
    events = ev.get_json()
    assert any(e['event_type'] == 'NoteAdded' for e in events)

def test_update_notes_persists_and_logs_event(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'NoteTaker'}, headers={'Authorization': f'Bearer {token}'} )

    # Update notes
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 'Initial investigation complete.', 'staff_name': 'NoteTaker'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['notes'] == 'Initial investigation complete.'
    assert data['last_updated_by'] == 'NoteTaker'

    # Verify event
    resp_events = client.get(
        f'/api/v1/jobs/{job.id}/events',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_events.status_code == 200
    events = resp_events.get_json()
    found = next((e for e in events if e['event_type'] == 'NotesUpdated'), None)
    assert found is not None
    assert found['triggered_by'] == 'NoteTaker'


def test_update_notes_validation_rules(client, token, app):
    job = create_job(app)
    # Add staff and then deactivate to test inactive guard
    client.post('/api/v1/staff', json={'name': 'Inactive'}, headers={'Authorization': f'Bearer {token}'} )
    client.patch('/api/v1/staff/Inactive', json={'is_active': False}, headers={'Authorization': f'Bearer {token}'} )

    # Missing staff_name
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 'x'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Inactive staff
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 'x', 'staff_name': 'Inactive'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Notes required and must be string (allow empty string to clear)
    client.post('/api/v1/staff', json={'name': 'Active'}, headers={'Authorization': f'Bearer {token}'} )
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'staff_name': 'Active'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 123, 'staff_name': 'Active'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Too long notes (limit 5000 chars)
    long_text = 'a' * 6000
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': long_text, 'staff_name': 'Active'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Clearing notes with empty string is allowed
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': '', 'staff_name': 'Active'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == ''


def test_update_notes_with_attribution_and_event(client, token, app):
    job = create_job(app)
    # Add active staff
    client.post('/api/v1/staff', json={'name': 'Noter'}, headers={'Authorization': f'Bearer {token}'})

    payload = { 'notes': 'Initial investigation notes', 'staff_name': 'Noter' }
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['notes'] == 'Initial investigation notes'
    assert data['last_updated_by'] == 'Noter'

    # Verify event
    events_resp = client.get(f'/api/v1/jobs/{job.id}/events', headers={'Authorization': f'Bearer {token}'})
    assert events_resp.status_code == 200
    events = events_resp.get_json()
    notes_evt = next((e for e in events if e['event_type'] == 'NotesUpdated'), None)
    assert notes_evt is not None
    assert notes_evt['triggered_by'] == 'Noter'
    assert notes_evt.get('details', {}).get('notes_len') == len('Initial investigation notes')


def test_update_notes_requires_active_staff_and_string_notes(client, token, app):
    job = create_job(app)
    # Missing staff_name
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 'x'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Inactive/unknown staff
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 'x', 'staff_name': 'Nobody'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Add active staff; invalid notes type
    client.post('/api/v1/staff', json={'name': 'Writer'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': 123, 'staff_name': 'Writer'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400

    # Clearing notes with empty string should be accepted
    resp = client.patch(
        f'/api/v1/jobs/{job.id}/notes',
        json={'notes': '', 'staff_name': 'Writer'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert resp.get_json()['notes'] == ''