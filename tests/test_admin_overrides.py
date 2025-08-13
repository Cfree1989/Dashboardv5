# type: ignore
import os
import json
from pathlib import Path
from app import db
from app.models.job import Job


STATUS_DIR = {
    'UPLOADED': 'Uploaded',
    'PENDING': 'Pending',
    'READYTOPRINT': 'ReadyToPrint',
    'PRINTING': 'Printing',
    'COMPLETED': 'Completed',
    'PAIDPICKEDUP': 'PaidPickedUp',
    'ARCHIVED': 'Archived',
}


def _write_files(tmp_path: Path, status: str, base_name: str = 'file') -> tuple[Path, Path]:
    d = tmp_path / STATUS_DIR[status]
    d.mkdir(parents=True, exist_ok=True)
    file_path = d / f'{base_name}.stl'
    file_path.write_text('model-data')
    meta_path = d / f'{base_name}_metadata.json'
    meta_path.write_text(json.dumps({'status': status}))
    return file_path, meta_path


def _create_job(app, file_path: Path, meta_path: Path, status: str = 'UPLOADED') -> str:
    with app.app_context():
        job = Job(
            student_name='Test', student_email='test@example.com', discipline='Art',
            class_number='101', original_filename=file_path.name, display_name=file_path.name,
            file_path=str(file_path), metadata_path=str(meta_path), printer='Prusa', color='Red', material='Filament',
            status=status,
        )
        db.session.add(job)
        db.session.commit()
        return job.id


def _add_staff(client, token, name='Admin User'):
    client.post('/api/v1/staff', json={'name': name}, headers={'Authorization': f'Bearer {token}'})


def test_admin_force_confirm_moves_and_logs(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # seed uploaded file; job in PENDING
    file_path, meta_path = _write_files(tmp_path, 'UPLOADED')
    job_id = _create_job(app, file_path, meta_path, status='PENDING')
    _add_staff(client, token)

    resp = client.post(
        f'/api/v1/jobs/{job_id}/admin/force-confirm',
        json={'staff_name': 'Admin User', 'reason': 'test'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'READYTOPRINT'
    # file moved
    new_path = tmp_path / 'ReadyToPrint' / file_path.name
    assert new_path.exists()
    assert not file_path.exists()
    # events contain admin entries
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = {e['event_type'] for e in events}
    assert 'AdminForceConfirm' in types
    assert 'AdminAction' in types


def test_admin_change_status_to_archived_moves_and_logs(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    file_path, meta_path = _write_files(tmp_path, 'COMPLETED')
    job_id = _create_job(app, file_path, meta_path, status='COMPLETED')
    _add_staff(client, token)

    resp = client.post(
        f'/api/v1/jobs/{job_id}/admin/change-status',
        json={'staff_name': 'Admin User', 'reason': 'cleanup', 'new_status': 'ARCHIVED'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ARCHIVED'
    new_path = tmp_path / 'Archived' / file_path.name
    assert new_path.exists()
    assert not file_path.exists()
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = {e['event_type'] for e in events}
    assert 'AdminStatusChanged' in types
    assert 'AdminAction' in types


def test_admin_mark_failed_moves_back_to_readytoprint(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    file_path, meta_path = _write_files(tmp_path, 'PRINTING')
    job_id = _create_job(app, file_path, meta_path, status='PRINTING')
    _add_staff(client, token)

    resp = client.post(
        f'/api/v1/jobs/{job_id}/admin/mark-failed',
        json={'staff_name': 'Admin User', 'reason': 'nozzle jam'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'READYTOPRINT'
    new_path = tmp_path / 'ReadyToPrint' / file_path.name
    assert new_path.exists()
    assert not file_path.exists()
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = {e['event_type'] for e in events}
    assert 'PrintFailed' in types
    assert 'AdminAction' in types


def test_admin_force_unlock_logs_action(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    file_path, meta_path = _write_files(tmp_path, 'UPLOADED')
    job_id = _create_job(app, file_path, meta_path, status='UPLOADED')
    _add_staff(client, token)

    resp = client.post(
        f'/api/v1/jobs/{job_id}/admin/force-unlock',
        json={'staff_name': 'Admin User', 'reason': 'stuck'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = {e['event_type'] for e in events}
    assert 'AdminAction' in types


def test_admin_resend_email_endpoint(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Create a PENDING job (awaiting student confirmation)
    file_path, meta_path = _write_files(tmp_path, 'UPLOADED')
    job_id = _create_job(app, file_path, meta_path, status='PENDING')
    _add_staff(client, token)

    resp = client.post(
        f'/api/v1/jobs/{job_id}/admin/resend-email',
        json={'staff_name': 'Admin User'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['job_id'] == job_id

    # Rate limit should block immediate second call
    resp2 = client.post(
        f'/api/v1/jobs/{job_id}/admin/resend-email',
        json={'staff_name': 'Admin User'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp2.status_code == 429

