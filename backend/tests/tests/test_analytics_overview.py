# type: ignore
from datetime import datetime, timedelta

from app import db
from app.models.job import Job
from app.models.event import Event


def _mk_job(app, *, printer: str, discipline: str) -> str:
    with app.app_context():
        job = Job(
            student_name='Test',
            student_email='test@example.com',
            discipline=discipline,
            class_number='101',
            original_filename='file.stl',
            display_name='file.stl',
            file_path='path',
            metadata_path='meta',
            printer=printer,
            color='Red',
            material='Filament',
            status='UPLOADED',
        )
        db.session.add(job)
        db.session.commit()
        return job.id


def _mk_reject_event(app, *, job_id: str, days_ago: int):
    with app.app_context():
        ts = datetime.utcnow() - timedelta(days=days_ago)
        ev = Event(
            job_id=job_id,
            timestamp=ts,
            event_type='JobRejected',
            details=None,
            triggered_by='Tester',
            workstation_id='WS1',
        )
        db.session.add(ev)
        db.session.commit()


def test_overview_recent_rejections_30d_window(client, token, app):
    jid_old = _mk_job(app, printer='Prusa', discipline='Art')
    jid_new = _mk_job(app, printer='Prusa', discipline='Art')
    _mk_reject_event(app, job_id=jid_old, days_ago=40)
    _mk_reject_event(app, job_id=jid_new, days_ago=3)

    resp = client.get('/api/v1/analytics/overview?days=7', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['recent_rejections'] == 1


def test_overview_recent_rejections_filters(client, token, app):
    jid_prusa = _mk_job(app, printer='Prusa', discipline='Art')
    jid_raise = _mk_job(app, printer='Raise3D', discipline='Engineering')
    _mk_reject_event(app, job_id=jid_prusa, days_ago=2)
    _mk_reject_event(app, job_id=jid_raise, days_ago=2)

    # Filter by printer
    r1 = client.get('/api/v1/analytics/overview?printer=Prusa', headers={'Authorization': f'Bearer {token}'})
    assert r1.status_code == 200
    assert r1.get_json()['recent_rejections'] == 1

    # Filter by discipline
    r2 = client.get('/api/v1/analytics/overview?discipline=Engineering', headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    assert r2.get_json()['recent_rejections'] == 1


