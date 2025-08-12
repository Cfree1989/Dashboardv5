from flask import Blueprint
from flask import jsonify, request
from app.models.event import Event
from app.models.job import Job
from app.models.payment import Payment
from app.utils.decorators import token_required
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

@bp.route('/overview', methods=['GET'])
@token_required
def overview():
    # Params
    try:
        days = int(request.args.get('days', 7))
    except Exception:
        days = 7
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    # Totals by status (queue view)
    q = Job.query
    if printer_filter:
        q = q.filter(Job.printer == printer_filter)
    if discipline_filter:
        q = q.filter(Job.discipline == discipline_filter)
    rows = q.with_entities(Job.status, func.count()).group_by(Job.status).all()
    by_status = {status: int(count) for status, count in rows}
    active_statuses = {'UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING'}
    in_queue = sum(by_status.get(s, 0) for s in active_statuses)
    # Totals
    total_submissions = q.count()
    # Avg turnaround (best-effort): from JobCreated to JobMarkedComplete events within range
    since = datetime.now(timezone.utc) - timedelta(days=days)
    completed_events = Event.query.filter(Event.event_type == 'JobMarkedComplete').all()
    diffs: list[float] = []
    # Build lookup of first JobCreated event per job
    created_by_job: dict[str, datetime] = {}
    for e in Event.query.filter(Event.event_type == 'JobCreated').all():
        if e.job_id not in created_by_job:
            created_by_job[e.job_id] = getattr(e, 'timestamp', None)
    for e in completed_events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= since:
            start = created_by_job.get(e.job_id)
            if start:
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                diffs.append((ts - start).total_seconds() / 3600.0)
    avg_turnaround_hours = round(sum(diffs) / len(diffs), 2) if diffs else None
    # Storage usage unknown without config; return None placeholder
    payload = {
        'by_status': by_status,
        'in_queue': in_queue,
        'total_submissions': total_submissions,
        'avg_turnaround_hours': avg_turnaround_hours,
        'storage_usage_percent': None,
        'recent_rejections_30d': Event.query.filter(Event.event_type == 'JobRejected').count(),
    }
    return jsonify(payload), 200


@bp.route('/trends', methods=['GET'])
@token_required
def trends():
    # Very lightweight stub: daily counts of JobCreated over N days
    try:
        days = int(request.args.get('days', 30))
    except Exception:
        days = 30
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    start = datetime.now(timezone.utc) - timedelta(days=days)
    # Fetch events and bucket by date
    events = Event.query.filter(Event.event_type == 'JobCreated').all()
    from collections import Counter
    bucket = Counter()
    for e in events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= start:
            bucket[ts.date().isoformat()] += 1
    series = [{'date': d, 'count': c} for d, c in sorted(bucket.items())]
    # Approvals series
    approvals_bucket = Counter()
    approvals = Event.query.filter(Event.event_type == 'StaffApproved').all()
    for e in approvals:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= start:
            # Only include approvals for jobs that match filters if specified
            if printer_filter or discipline_filter:
                job = Job.query.get(e.job_id)
                if printer_filter and getattr(job, 'printer', None) != printer_filter:
                    continue
                if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
                    continue
            approvals_bucket[ts.date().isoformat()] += 1
    approvals_series = [{'date': d, 'count': c} for d, c in sorted(approvals_bucket.items())]
    return jsonify({'series': series, 'approvals': approvals_series, 'metric': 'submissions'}), 200


@bp.route('/resources', methods=['GET'])
@token_required
def resources():
    try:
        days = int(request.args.get('days', 7))
    except Exception:
        days = 7
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    since = datetime.now(timezone.utc) - timedelta(days=days)
    # Printing throughput (JobMarkedPrinting per day)
    from collections import Counter, defaultdict
    throughput = Counter()
    per_printer = defaultdict(lambda: Counter())
    printing_events = Event.query.filter(Event.event_type == 'JobMarkedPrinting').all()
    for e in printing_events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= since:
            d = ts.date().isoformat()
            throughput[d] += 1
            # attribute printer if known
            job = Job.query.get(e.job_id)
            printer = getattr(job, 'printer', None) or 'Unknown'
            if printer_filter and printer != printer_filter:
                # Skip if not matching printer filter
                continue
            if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
                continue
            per_printer[printer][d] += 1
    printing_throughput = [{'date': d, 'count': c} for d, c in sorted(throughput.items())]
    printer_utilization = [
        {'printer': p, 'series': [{'date': d, 'count': c} for d, c in sorted(series.items())]}
        for p, series in per_printer.items()
    ]
    # Average lead time series (JobCreated to JobMarkedComplete average per day)
    # Build created timestamp per job
    created_map: dict[str, datetime] = {}
    for e in Event.query.filter(Event.event_type == 'JobCreated').all():
        if e.job_id not in created_map:
            created_map[e.job_id] = getattr(e, 'timestamp', None)
    # Gather completion diffs by day
    from collections import defaultdict as dd
    day_diffs: dict[str, list[float]] = dd(list)
    completed_events = Event.query.filter(Event.event_type == 'JobMarkedComplete').all()
    for e in completed_events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= since:
            start = created_map.get(e.job_id)
            if start:
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                day_diffs[ts.date().isoformat()].append((ts - start).total_seconds() / 3600.0)
    average_lead_time = [
        {'date': d, 'hours': round(sum(vals)/len(vals), 2)} for d, vals in sorted(day_diffs.items()) if vals
    ]
    # Material consumption from payments (grams by material over period)
    filament_g = 0.0
    resin_g = 0.0
    payments = Payment.query.all()
    for p in payments:
        job = Job.query.get(p.job_id)
        mat = (getattr(job, 'material', '') or '').strip().lower()
        if mat == 'resin':
            resin_g += float(getattr(p, 'grams', 0) or 0)
        else:
            filament_g += float(getattr(p, 'grams', 0) or 0)
    # Queue age distribution (active jobs)
    now = datetime.now(timezone.utc)
    active_statuses = {'UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING'}
    buckets = {'0-2': 0, '3-7': 0, '7+': 0}
    jq = Job.query.filter(Job.status.in_(list(active_statuses)))
    if printer_filter:
        jq = jq.filter(Job.printer == printer_filter)
    if discipline_filter:
        jq = jq.filter(Job.discipline == discipline_filter)
    for j in jq.all():
        created = getattr(j, 'created_at', None)
        if not created:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_old = (now - created).days
        if days_old <= 2:
            buckets['0-2'] += 1
        elif days_old <= 7:
            buckets['3-7'] += 1
        else:
            buckets['7+'] += 1
    # Revenue over time from payments
    revenue_counter = Counter()
    for p in payments:
        ts = getattr(p, 'paid_ts', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= since:
            revenue_counter[ts.date().isoformat()] += int(getattr(p, 'price_cents', 0) or 0)
    revenue_over_time = [{'date': d, 'cents': c} for d, c in sorted(revenue_counter.items())]
    # Payment metrics
    total_revenue_cents = sum(c for _, c in revenue_counter.items())
    payment_count = len(payments)
    avg_ticket_usd = round((total_revenue_cents / 100.0) / payment_count, 2) if payment_count else 0.0
    # Build payload
    payload = {
        'printing_throughput': printing_throughput,
        'average_lead_time': average_lead_time,
        'printer_utilization': printer_utilization,
        'material_consumption_g': {'filament': filament_g, 'resin': resin_g},
        'queue_age_buckets': buckets,
        'revenue_over_time': revenue_over_time,
        'total_revenue_cents': total_revenue_cents,
        'avg_ticket_usd': avg_ticket_usd,
        'payment_count': payment_count,
    }
    return jsonify(payload), 200

@bp.route('/events', methods=['GET'])
@token_required
def list_events():
    events = Event.query.all()
    return jsonify([e.to_dict() for e in events]), 200 