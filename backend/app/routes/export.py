from flask import Blueprint, request, g, Response
from datetime import datetime
from io import StringIO
import csv

from app import db
from app.models.payment import Payment
from app.models.job import Job
from app.models.event import Event
from app.models.staff import Staff
from app.business_logic.shared_services.response_service import ResponseService, ErrorCategory, ErrorCode
from app.utils.decorators import token_required


bp = Blueprint('export', __name__, url_prefix='/api/v1/export')


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return 'invalid'


@bp.route('/payments', methods=['POST'])
@token_required
def export_payments():
    data = request.get_json(silent=True) or {}

    # Validate staff attribution
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return ResponseService.validation_error(
            message='staff_name is required',
            error_code=ErrorCode.MISSING_REQUIRED_FIELD.value
        )
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return ResponseService.validation_error(
            message='Invalid or inactive staff_name',
            error_code=ErrorCode.INVALID_VALUE.value
        )

    start_date = _parse_date(data.get('start_date'))
    end_date = _parse_date(data.get('end_date'))
    if start_date == 'invalid' or end_date == 'invalid':
        return ResponseService.validation_error(
            message='Invalid date format. Use YYYY-MM-DD',
            error_code=ErrorCode.INVALID_FORMAT.value
        )
    # If only one bound provided, allow open-ended filtering
    # If neither provided, default to no filtering (all rows)

    # Build query joining Payment and Job for richer export data
    q = db.session.query(Payment, Job).join(Job, Payment.job_id == Job.id)
    if start_date:
        q = q.filter(Payment.paid_ts >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        q = q.filter(Payment.paid_ts <= datetime.combine(end_date, datetime.max.time()))
    rows = q.all()

    # Prepare CSV
    output = StringIO()
    writer = csv.writer(output)
    headers = [
        'job_id', 'student_name', 'student_email', 'discipline', 'material', 'printer',
        'grams', 'price_cents', 'price_usd', 'txn_no', 'picked_up_by', 'paid_ts', 'paid_by_staff'
    ]
    writer.writerow(headers)
    for payment, job in rows:
        price_usd = (payment.price_cents or 0) / 100.0
        writer.writerow([
            payment.job_id,
            getattr(job, 'student_name', ''),
            getattr(job, 'student_email', ''),
            getattr(job, 'discipline', ''),
            getattr(job, 'material', ''),
            getattr(job, 'printer', ''),
            payment.grams,
            payment.price_cents,
            f"{price_usd:.2f}",
            payment.txn_no,
            payment.picked_up_by,
            payment.paid_ts.isoformat() if payment.paid_ts else '',
            payment.paid_by_staff,
        ])

    csv_data = output.getvalue()

    # Log export event
    evt_details = {
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'count': len(rows),
        'format': 'csv',
    }
    evt = Event(
        job_id='system',
        event_type='PaymentsExported',
        details=evt_details,
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', 'unknown'),
    )
    db.session.add(evt)
    db.session.commit()

    # Filename
    start_token = (data.get('start_date') or 'all').replace('-', '')
    end_token = (data.get('end_date') or 'all').replace('-', '')
    filename = f'payments_{start_token}_{end_token}.csv'

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


