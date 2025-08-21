# type: ignore
import os
import json
from pathlib import Path
from app import db
from app.models.job import Job
from app.services.token_service import generate_confirmation_token


def _write_initial_files(tmp_path: Path) -> tuple[Path, Path]:
    uploaded_dir = tmp_path / 'Uploaded'
    uploaded_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploaded_dir / 'file.stl'
    file_path.write_text('model-data')
    meta_path = uploaded_dir / 'file_metadata.json'
    meta_path.write_text(json.dumps({'status': 'UPLOADED'}))
    return file_path, meta_path


def test_filesystem_transitions_and_metadata_sync(client, token, app, tmp_path):
    os.environ['STORAGE_PATH'] = str(tmp_path)

    # Seed initial file + metadata in Uploaded/
    file_path, meta_path = _write_initial_files(tmp_path)

    # Create a job bound to those files
    with app.app_context():
        job = Job(
            student_name='Test', student_email='test@example.com', discipline='Art',
            class_number='101', original_filename='file.stl', display_name='file.stl',
            file_path=str(file_path), metadata_path=str(meta_path), printer='Prusa', color='Red', material='Filament'
        )
        db.session.add(job)
        db.session.commit()
        job_id = job.id

    # Add staff for actions
    client.post('/api/v1/staff', json={'name': 'Operator'}, headers={'Authorization': f'Bearer {token}'})

    # Approve (no move expected, only metadata sync to PENDING)
    resp = client.post(
        f'/api/v1/jobs/{job_id}/approve',
        json={'staff_name': 'Operator', 'weight_g': 10, 'time_hours': 1, 'authoritative_filename': 'file.stl'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'PENDING'
    # File still in Uploaded
    assert file_path.exists()
    # Metadata updated in place
    meta = json.loads((tmp_path / 'Uploaded' / 'file_metadata.json').read_text())
    assert meta.get('status') == 'PENDING'
    assert meta.get('authoritative_filename') == 'file.stl'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Confirm (moves to ReadyToPrint)
    with app.app_context():
        token_val = generate_confirmation_token(job_id)
    resp = client.post(f'/api/v1/submit/confirm/{token_val}')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'READYTOPRINT'
    # File moved: now in ReadyToPrint, not in Uploaded
    new_path = tmp_path / 'ReadyToPrint' / 'file.stl'
    new_meta = tmp_path / 'ReadyToPrint' / 'file_metadata.json'
    assert new_path.exists()
    assert not file_path.exists()
    assert new_meta.exists()
    meta = json.loads(new_meta.read_text())
    assert meta.get('status') == 'READYTOPRINT'
    assert meta.get('authoritative_filename') == 'file.stl'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Mark Printing (moves to Printing)
    resp = client.post(
        f'/api/v1/jobs/{job_id}/mark-printing',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert not new_path.exists()
    printing_path = tmp_path / 'Printing' / 'file.stl'
    printing_meta = tmp_path / 'Printing' / 'file_metadata.json'
    assert printing_path.exists()
    meta = json.loads(printing_meta.read_text())
    assert meta.get('status') == 'PRINTING'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Mark Complete (moves to Completed)
    resp = client.post(
        f'/api/v1/jobs/{job_id}/mark-complete',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert not printing_path.exists()
    completed_path = tmp_path / 'Completed' / 'file.stl'
    completed_meta = tmp_path / 'Completed' / 'file_metadata.json'
    assert completed_path.exists()
    meta = json.loads(completed_meta.read_text())
    assert meta.get('status') == 'COMPLETED'
    assert Path(meta.get('file_path')).name == 'file.stl'

    # Mark Picked Up (moves to PaidPickedUp)
    resp = client.post(
        f'/api/v1/jobs/{job_id}/mark-picked-up',
        json={'staff_name': 'Operator'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert not completed_path.exists()
    final_path = tmp_path / 'PaidPickedUp' / 'file.stl'
    final_meta = tmp_path / 'PaidPickedUp' / 'file_metadata.json'
    assert final_path.exists()
    meta = json.loads(final_meta.read_text())
    assert meta.get('status') == 'PAIDPICKEDUP'
    assert Path(meta.get('file_path')).name == 'file.stl'
    assert meta.get('authoritative_filename') == 'file.stl'


