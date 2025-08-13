# type: ignore
from datetime import datetime, timedelta

from app import db
from app.models.job import Job
from app.models.payment import Payment


def _paid_job(app, *, days_ago: int, grams: float, price_cents: int, printer: str = 'Prusa', discipline: str = 'Art', material: str = 'Filament'):
    with app.app_context():
        j = Job(
            student_name='T',
            student_email='t@example.com',
            discipline=discipline,
            class_number='101',
            original_filename='f.stl',
            display_name='f.stl',
            file_path='p',
            metadata_path='m',
            printer=printer,
            color='Red',
            material=material,
            status='PAIDPICKEDUP',
        )
        db.session.add(j)
        db.session.flush()
        p = Payment(
            job_id=j.id,
            grams=grams,
            price_cents=price_cents,
            txn_no='X',
            picked_up_by='Stu',
            paid_ts=datetime.utcnow() - timedelta(days=days_ago),
            paid_by_staff='Cashier'
        )
        db.session.add(p)
        db.session.commit()


def test_resources_respects_days_window(client, token, app):
    _paid_job(app, days_ago=5, grams=10.0, price_cents=1000, material='Filament')
    _paid_job(app, days_ago=40, grams=20.0, price_cents=2000, material='Resin')

    resp = client.get('/api/v1/analytics/resources?days=30', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['material_consumption_g']['filament'] == 10.0
    assert data['material_consumption_g']['resin'] == 0.0
    assert data['payment_count'] == 1
    # Revenue over time only includes recent payment
    assert sum(pt['cents'] for pt in data['revenue_over_time']) == 1000


def test_resources_filters_by_printer_and_discipline(client, token, app):
    _paid_job(app, days_ago=1, grams=10.0, price_cents=1000, printer='Prusa', discipline='Art', material='Filament')
    _paid_job(app, days_ago=1, grams=15.0, price_cents=1500, printer='Raise3D', discipline='Engineering', material='Filament')

    r1 = client.get('/api/v1/analytics/resources?days=7&printer=Prusa', headers={'Authorization': f'Bearer {token}'})
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1['material_consumption_g']['filament'] == 10.0
    assert d1['payment_count'] == 1

    r2 = client.get('/api/v1/analytics/resources?days=7&discipline=Engineering', headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert d2['material_consumption_g']['filament'] == 15.0
    assert d2['payment_count'] == 1


