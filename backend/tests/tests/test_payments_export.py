# type: ignore
import io
import csv
from datetime import datetime, timedelta

from app import db
from app.models.job import Job
from app.models.payment import Payment


def _create_paid_job(app, student_name: str, price_cents: int, paid_ts: datetime):
    with app.app_context():
        job = Job(
            student_name=student_name,
            student_email=f"{student_name.lower()}@example.com",
            discipline='Art',
            class_number='101',
            original_filename='file.stl',
            display_name='file.stl',
            file_path='path',
            metadata_path='meta',
            printer='Prusa',
            color='Red',
            material='Filament',
            status='PAIDPICKEDUP',
        )
        db.session.add(job)
        db.session.flush()
        pay = Payment(
            job_id=job.id,
            grams=10.0,
            price_cents=price_cents,
            txn_no='TXN',
            picked_up_by='Student',
            paid_ts=paid_ts,
            paid_by_staff='Cashier',
        )
        db.session.add(pay)
        db.session.commit()
        return job.id


def test_export_payments_csv_happy_path(client, token, app):
    # Seed staff for attribution
    client.post('/api/v1/staff', json={'name': 'Reporter'}, headers={'Authorization': f'Bearer {token}'})

    now = datetime.utcnow()
    _create_paid_job(app, 'Alice', 500, now - timedelta(days=10))
    _create_paid_job(app, 'Bob', 700, now - timedelta(days=3))

    start = (now - timedelta(days=7)).date().isoformat()
    end = now.date().isoformat()

    resp = client.post(
        '/api/v1/export/payments',
        json={'start_date': start, 'end_date': end, 'staff_name': 'Reporter'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    assert 'text/csv' in resp.content_type
    assert 'attachment; filename=' in resp.headers.get('Content-Disposition', '')

    # Parse CSV and verify headers and at least Bob row present
    content = resp.data.decode('utf-8')
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert rows[0] == [
        'job_id', 'student_name', 'student_email', 'discipline', 'material', 'printer',
        'grams', 'price_cents', 'price_usd', 'txn_no', 'picked_up_by', 'paid_ts', 'paid_by_staff'
    ]
    assert any(r[1] == 'Bob' for r in rows[1:])

    # Event logged
    ev = client.get('/api/v1/analytics/events', headers={'Authorization': f'Bearer {token}'})
    assert ev.status_code == 200
    events = ev.get_json()
    assert any(e['event_type'] == 'PaymentsExported' for e in events)


def test_export_payments_invalid_date(client, token):
    client.post('/api/v1/staff', json={'name': 'Reporter'}, headers={'Authorization': f'Bearer {token}'})
    resp = client.post(
        '/api/v1/export/payments',
        json={'start_date': '2024-13-01', 'staff_name': 'Reporter'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 400
    assert 'Invalid date format' in (resp.get_json() or {}).get('message', '')


