# type: ignore
import io
from datetime import datetime, timedelta

import pytest

from app import db
from app.models.job import Job
from app.models.payment import Payment


def _create_paid_job(app, *, student_name: str, price_cents: int, paid_ts: datetime, printer: str = 'Prusa', discipline: str = 'Art', material: str = 'Filament'):
    with app.app_context():
        job = Job(
            student_name=student_name,
            student_email=f"{student_name.lower()}@example.com",
            discipline=discipline,
            class_number='101',
            original_filename='file.stl',
            display_name='file.stl',
            file_path='path',
            metadata_path='meta',
            printer=printer,
            color='Red',
            material=material,
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


def test_financial_requires_auth(client):
    resp = client.get('/api/v1/analytics/financial')
    assert resp.status_code == 401


def test_financial_happy_path(client, token, app):
    now = datetime.utcnow()
    _create_paid_job(app, student_name='Alice', price_cents=500, paid_ts=now - timedelta(days=10))
    _create_paid_job(app, student_name='Bob', price_cents=700, paid_ts=now - timedelta(days=3))
    _create_paid_job(app, student_name='Carol', price_cents=1300, paid_ts=now - timedelta(days=40))

    resp = client.get(
        '/api/v1/analytics/financial?days=30',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_revenue_cents'] == 1200  # Alice + Bob
    assert data['payment_count'] == 2
    assert pytest.approx(data['avg_ticket_usd'], rel=1e-3) == round((1200 / 100.0) / 2, 2)
    # Revenue over time should contain two entries (possibly on different dates)
    dates = {p['date'] for p in data['revenue_over_time']}
    assert len(dates) >= 1


def test_financial_filters_by_printer_and_discipline(client, token, app):
    now = datetime.utcnow()
    _create_paid_job(app, student_name='P1', price_cents=1000, paid_ts=now - timedelta(days=1), printer='Prusa', discipline='Art')
    _create_paid_job(app, student_name='P2', price_cents=2000, paid_ts=now - timedelta(days=1), printer='Raise3D', discipline='Engineering')

    # Filter by printer
    resp_printer = client.get(
        '/api/v1/analytics/financial?days=7&printer=Prusa',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_printer.status_code == 200
    data_p = resp_printer.get_json()
    assert data_p['total_revenue_cents'] == 1000
    assert data_p['payment_count'] == 1

    # Filter by discipline
    resp_disc = client.get(
        '/api/v1/analytics/financial?days=7&discipline=Engineering',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp_disc.status_code == 200
    data_d = resp_disc.get_json()
    assert data_d['total_revenue_cents'] == 2000
    assert data_d['payment_count'] == 1


def test_financial_no_payments_returns_zeros(client, token):
    resp = client.get(
        '/api/v1/analytics/financial?days=30',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_revenue_cents'] == 0
    assert data['payment_count'] == 0
    assert data['avg_ticket_usd'] == 0
    assert data['revenue_over_time'] == []
    assert data['estimated_revenue_cents'] == 0
    assert data['actual_revenue_cents'] == 0
    assert data['variance_cents'] == 0


def test_financial_estimated_vs_actual_revenue(client, token, app):
    """Test estimated vs actual revenue calculation with mixed materials and min-charge cases"""
    now = datetime.utcnow()
    
    # Create jobs with cost estimates (but no payments yet)
    with app.app_context():
        # Job 1: Filament job with $5.00 estimate
        job1 = Job(
            student_name='Alice',
            student_email='alice@example.com',
            discipline='Art',
            class_number='101',
            original_filename='file1.stl',
            display_name='file1.stl',
            file_path='path1',
            metadata_path='meta1',
            printer='Prusa',
            color='Red',
            material='Filament',
            status='UPLOADED',
            cost_usd=5.00,
            created_at=now - timedelta(days=5)
        )
        db.session.add(job1)
        
        # Job 2: Resin job with $8.00 estimate  
        job2 = Job(
            student_name='Bob',
            student_email='bob@example.com',
            discipline='Engineering',
            class_number='201',
            original_filename='file2.stl',
            display_name='file2.stl',
            file_path='path2',
            metadata_path='meta2',
            printer='Formlabs',
            color='True Black',
            material='Resin',
            status='UPLOADED',
            cost_usd=8.00,
            created_at=now - timedelta(days=3)
        )
        db.session.add(job2)
        
        # Job 3: Small resin job that will hit minimum charge
        job3 = Job(
            student_name='Carol',
            student_email='carol@example.com',
            discipline='Art',
            class_number='101',
            original_filename='file3.stl',
            display_name='file3.stl',
            file_path='path3',
            metadata_path='meta3',
            printer='Formlabs',
            color='White',
            material='Resin',
            status='UPLOADED',
            cost_usd=1.00,  # Small estimate
            created_at=now - timedelta(days=1)
        )
        db.session.add(job3)
        db.session.commit()
        
        # Create payments for jobs 1 and 3 (job 2 not paid yet)
        pay1 = Payment(
            job_id=job1.id,
            grams=50.0,  # 50g filament = $5.00
            price_cents=500,
            txn_no='TXN1',
            picked_up_by='Alice',
            paid_ts=now - timedelta(days=2),
            paid_by_staff='Cashier',
        )
        db.session.add(pay1)
        
        pay3 = Payment(
            job_id=job3.id,
            grams=10.0,  # 10g resin = $2.00, but minimum charge applies = $3.00
            price_cents=300,
            txn_no='TXN3',
            picked_up_by='Carol',
            paid_ts=now - timedelta(days=1),
            paid_by_staff='Cashier',
        )
        db.session.add(pay3)
        db.session.commit()

    # Test the financial endpoint
    resp = client.get(
        '/api/v1/analytics/financial?days=30',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    
    # Estimated revenue: $5.00 + $8.00 + $1.00 = $14.00 = 1400 cents
    assert data['estimated_revenue_cents'] == 1400
    
    # Actual revenue: $5.00 + $3.00 = $8.00 = 800 cents (only paid jobs)
    assert data['actual_revenue_cents'] == 800
    
    # Variance: $8.00 - $14.00 = -$6.00 = -600 cents (negative because actual < estimated)
    assert data['variance_cents'] == -600
    
    # Verify other fields still work
    assert data['total_revenue_cents'] == 800
    assert data['payment_count'] == 2


