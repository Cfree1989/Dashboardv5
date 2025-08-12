# type: ignore
import os
import json
from pathlib import Path
from app import db
from app.models.job import Job


def _seed_file(tmp_path: Path, status_dir: str, name: str = 'file.stl') -> tuple[Path, Path]:
    base = tmp_path / status_dir
    base.mkdir(parents=True, exist_ok=True)
    f = base / name
    m = base / 'file_metadata.json'
    f.write_text('data')
    m.write_text(json.dumps({'status': status_dir.upper()}))
    return f, m


def test_revert_completion_moves_file_and_logs(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Seed in Completed
    f, m = _seed_file(tmp_path, 'Completed')
    with app.app_context():
        job = Job(
            student_name='S', student_email='s@example.com', discipline='X', class_number='101',
            original_filename='file.stl', display_name='file.stl', file_path=str(f), metadata_path=str(m),
            printer='Prusa', color='Red', material='Filament', status='COMPLETED'
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
    # Ensure staff
    client.post('/api/v1/staff', json={'name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})

    # Revert completion
    resp = client.post(f'/api/v1/jobs/{job_id}/revert-completion', json={'staff_name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'PRINTING'
    # Files moved
    assert not f.exists()
    dest = tmp_path / 'Printing' / 'file.stl'
    dest_meta = tmp_path / 'Printing' / 'file_metadata.json'
    assert dest.exists() and dest_meta.exists()
    meta = json.loads(dest_meta.read_text())
    assert meta.get('status') == 'PRINTING'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Guard: wrong status
    resp2 = client.post(f'/api/v1/jobs/{job_id}/revert-completion', json={'staff_name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})
    assert resp2.status_code == 400


def test_revert_pickup_moves_file_and_logs(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)
    # Seed in PaidPickedUp
    f, m = _seed_file(tmp_path, 'PaidPickedUp')
    with app.app_context():
        job = Job(
            student_name='S', student_email='s@example.com', discipline='X', class_number='101',
            original_filename='file.stl', display_name='file.stl', file_path=str(f), metadata_path=str(m),
            printer='Prusa', color='Red', material='Filament', status='PAIDPICKEDUP'
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id
    # Ensure staff
    client.post('/api/v1/staff', json={'name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})

    # Revert pickup
    resp = client.post(f'/api/v1/jobs/{job_id}/revert-pickup', json={'staff_name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'COMPLETED'
    # Files moved
    assert not f.exists()
    dest = tmp_path / 'Completed' / 'file.stl'
    dest_meta = tmp_path / 'Completed' / 'file_metadata.json'
    assert dest.exists() and dest_meta.exists()
    meta = json.loads(dest_meta.read_text())
    assert meta.get('status') == 'COMPLETED'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Guard: wrong status
    resp2 = client.post(f'/api/v1/jobs/{job_id}/revert-pickup', json={'staff_name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})
    assert resp2.status_code == 400
