# type: ignore
import os
import json
from pathlib import Path
from app import db
from app.models.job import Job


def _seed_file(tmp_path: Path, status: str, name: str = 'file.stl') -> tuple[Path, Path]:
    status_to_dir = {
        'UPLOADED': 'Uploaded',
        'PENDING': 'Pending',
        'READYTOPRINT': 'ReadyToPrint',
        'PRINTING': 'Printing',
        'COMPLETED': 'Completed',
        'PAIDPICKEDUP': 'PaidPickedUp',
    }
    d = tmp_path / status_to_dir[status]
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    f.write_text('data')
    m = d / f'{Path(name).stem}_metadata.json'
    m.write_text(json.dumps({'status': status}))
    return f, m


def _create_job(app, status: str, file_path: Path, meta_path: Path) -> str:
    with app.app_context():
        j = Job(
            student_name='Student', student_email='s@example.com', discipline='Art', class_number='101',
            original_filename=file_path.name, display_name=file_path.name, file_path=str(file_path), metadata_path=str(meta_path),
            printer='Prusa', color='Red', material='Filament', status=status,
        )
        db.session.add(j)
        db.session.commit()
        return j.id


def _add_staff(client, token, name='Operator'):
    client.post('/api/v1/staff', json={'name': name}, headers={'Authorization': f'Bearer {token}'})


def test_rejection_email_event_logged(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    file_path, meta_path = _seed_file(tmp_path, 'UPLOADED')
    job_id = _create_job(app, 'UPLOADED', file_path, meta_path)
    _add_staff(client, token, 'Operator')
    reasons = ['Scale issue', 'Wall too thin']
    resp = client.post(
        f'/api/v1/jobs/{job_id}/reject',
        json={'staff_name': 'Operator', 'reasons': reasons},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = [e['event_type'] for e in events]
    assert 'RejectionEmailSent' in types


def test_completion_email_event_logged(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    file_path, meta_path = _seed_file(tmp_path, 'PRINTING')
    job_id = _create_job(app, 'PRINTING', file_path, meta_path)
    _add_staff(client, token, 'Operator')
    resp = client.post(
        f'/api/v1/jobs/{job_id}/mark-complete',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    events = client.get(f'/api/v1/jobs/{job_id}/events', headers={'Authorization': f'Bearer {token}'}).get_json()
    types = [e['event_type'] for e in events]
    assert 'CompletionEmailSent' in types


