# type: ignore
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from app import db
from app.models.job import Job


def _seed(tmp_path: Path, status: str, name: str) -> tuple[Path, Path]:
    dirmap = {
        'UPLOADED': 'Uploaded',
        'PENDING': 'Pending',
        'READYTOPRINT': 'ReadyToPrint',
        'PRINTING': 'Printing',
        'COMPLETED': 'Completed',
        'PAIDPICKEDUP': 'PaidPickedUp',
        'ARCHIVED': 'Archived',
        'REJECTED': 'Uploaded',
    }
    d = tmp_path / dirmap[status]
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    f.write_text('data')
    m = d / f'{Path(name).stem}_metadata.json'
    m.write_text(json.dumps({'status': status}))
    return f, m


def _create_job(app, status: str, file_path: Path, meta_path: Path, created_at: datetime) -> str:
    with app.app_context():
        j = Job(
            student_name='S', student_email='s@example.com', discipline='Art', class_number='101',
            original_filename=file_path.name, display_name=file_path.name,
            file_path=str(file_path), metadata_path=str(meta_path), printer='Prusa', color='Red', material='Filament',
            status=status, created_at=created_at,
        )
        db.session.add(j)
        db.session.commit()
        return j.id


def _add_staff(client, token, name='Admin User'):
    client.post('/api/v1/staff', json={'name': name}, headers={'Authorization': f'Bearer {token}'})


def test_admin_archive_moves_and_logs(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    old = datetime.utcnow() - timedelta(days=60)
    # PaidPickedUp eligible
    fp1, mp1 = _seed(tmp_path, 'PAIDPICKEDUP', 'one.stl')
    job1 = _create_job(app, 'PAIDPICKEDUP', fp1, mp1, created_at=old)
    # Rejected eligible
    fp2, mp2 = _seed(tmp_path, 'UPLOADED', 'two.stl')
    job2 = _create_job(app, 'REJECTED', fp2, mp2, created_at=old)
    _add_staff(client, token)
    resp = client.post('/api/v1/admin/archive', json={'staff_name': 'Admin User', 'retention_days': 45}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['jobs_archived'] >= 2
    # Files should be in Archived
    assert (tmp_path / 'Archived' / 'one.stl').exists()
    assert (tmp_path / 'Archived' / 'two.stl').exists()


def test_admin_prune_deletes_archived(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    old = datetime.utcnow() - timedelta(days=400)
    # Archived eligible for prune
    fp, mp = _seed(tmp_path, 'ARCHIVED', 'old.stl')
    job_id = _create_job(app, 'ARCHIVED', fp, mp, created_at=old)
    _add_staff(client, token)
    resp = client.post('/api/v1/admin/prune', json={'staff_name': 'Admin User', 'retention_days': 365}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    # Job deleted from DB
    with app.app_context():
        assert db.session.get(Job, job_id) is None
    # Files removed
    assert not fp.exists() and not mp.exists()


