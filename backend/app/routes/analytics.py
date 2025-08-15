from flask import Blueprint
from flask import jsonify, request, current_app
from app.models.event import Event
from app.models.job import Job
from app.models.payment import Payment
from app.models.staff import Staff
from app.utils.decorators import token_required
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from time import time
import os

bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

# Lightweight in-memory cache for analytics responses (disabled during tests)
_AN_CACHE: dict = {}
_AN_CACHE_TTL = int(os.environ.get('ANALYTICS_CACHE_TTL', '60'))


def _cache_get(key: tuple):
    try:
        if current_app.config.get('TESTING'):
            return None
    except Exception:
        # If app context not ready, skip cache
        return None
    entry = _AN_CACHE.get(key)
    if not entry:
        return None
    expires_at, data = entry
    if time() >= expires_at:
        try:
            del _AN_CACHE[key]
        except Exception:
            pass
        return None
    return data


def _cache_set(key: tuple, data):
    try:
        if current_app.config.get('TESTING'):
            return
    except Exception:
        return
    _AN_CACHE[key] = (time() + _AN_CACHE_TTL, data)


def _parse_date_range():
    """Parse date range from query parameters"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        # Use custom date range
        try:
            start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            return start, end
        except ValueError:
            # Fall back to days parameter
            pass
    
    # Use days parameter (default 7 days)
    days = int(request.args.get('days', 7))
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return start, end


@bp.route('/overview', methods=['GET'])
@token_required
def overview():
    cache_key = ('overview', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
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
    completed_events = Event.query.filter(
        Event.event_type == 'JobMarkedComplete',
        Event.timestamp >= start,
        Event.timestamp <= end
    ).all()
    
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
        
        start_time = created_by_job.get(e.job_id)
        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            diffs.append((ts - start_time).total_seconds() / 3600.0)
    
    avg_turnaround_hours = round(sum(diffs) / len(diffs), 2) if diffs else None
    
    # Storage usage unknown without config; return None placeholder
    
    # Recent rejections in date range respecting filters
    rej_q = Event.query.filter(
        Event.event_type == 'JobRejected',
        Event.timestamp >= start,
        Event.timestamp <= end
    )
    
    recent_rejections = 0
    for e in rej_q.all():
        if printer_filter or discipline_filter:
            j = Job.query.get(e.job_id)
            if printer_filter and getattr(j, 'printer', None) != printer_filter:
                continue
            if discipline_filter and getattr(j, 'discipline', None) != discipline_filter:
                continue
        recent_rejections += 1
    
    payload = {
        'by_status': by_status,
        'in_queue': in_queue,
        'total_submissions': total_submissions,
        'avg_turnaround_hours': avg_turnaround_hours,
        'storage_usage_percent': None,
        'recent_rejections': recent_rejections,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/trends', methods=['GET'])
@token_required
def trends():
    cache_key = ('trends', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    
    # Fetch events and bucket by date
    events = Event.query.filter(
        Event.event_type == 'JobCreated',
        Event.timestamp >= start,
        Event.timestamp <= end
    ).all()
    
    from collections import Counter
    bucket = Counter()
    for e in events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        bucket[ts.date().isoformat()] += 1
    
    series = [{'date': d, 'count': c} for d, c in sorted(bucket.items())]
    
    # Approvals series
    approvals_bucket = Counter()
    approvals = Event.query.filter(
        Event.event_type == 'StaffApproved',
        Event.timestamp >= start,
        Event.timestamp <= end
    ).all()
    
    for e in approvals:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        # Only include approvals for jobs that match filters if specified
        if printer_filter or discipline_filter:
            job = Job.query.get(e.job_id)
            if printer_filter and getattr(job, 'printer', None) != printer_filter:
                continue
            if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
                continue
        approvals_bucket[ts.date().isoformat()] += 1
    
    approvals_series = [{'date': d, 'count': c} for d, c in sorted(approvals_bucket.items())]
    
    # Staff attribution for trends
    staff_submissions = Counter()
    staff_approvals = Counter()
    
    for e in events:
        staff_submissions[e.triggered_by] += 1
    
    for e in approvals:
        staff_approvals[e.triggered_by] += 1
    
    payload = {
        'series': series, 
        'approvals': approvals_series, 
        'metric': 'submissions',
        'staff_submissions': dict(staff_submissions),
        'staff_approvals': dict(staff_approvals),
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/resources', methods=['GET'])
@token_required
def resources():
    cache_key = ('resources', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    
    # Printing throughput (JobMarkedPrinting per day)
    from collections import Counter, defaultdict
    throughput = Counter()
    per_printer = defaultdict(lambda: Counter())
    printing_events = Event.query.filter(
        Event.event_type == 'JobMarkedPrinting',
        Event.timestamp >= start,
        Event.timestamp <= end
    ).all()
    
    for e in printing_events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
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
    completed_events = Event.query.filter(
        Event.event_type == 'JobMarkedComplete',
        Event.timestamp >= start,
        Event.timestamp <= end
    ).all()
    
    for e in completed_events:
        ts = getattr(e, 'timestamp', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        start_time = created_map.get(e.job_id)
        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            day_diffs[ts.date().isoformat()].append((ts - start_time).total_seconds() / 3600.0)
    
    average_lead_time = [
        {'date': d, 'hours': round(sum(vals)/len(vals), 2)} for d, vals in sorted(day_diffs.items()) if vals
    ]
    
    # Material consumption from payments (grams by material over period) with filters
    filament_g = 0.0
    resin_g = 0.0
    payments = Payment.query.filter(
        Payment.paid_ts >= start,
        Payment.paid_ts <= end
    ).all()
    
    for p in payments:
        ts = getattr(p, 'paid_ts', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        job = Job.query.get(p.job_id)
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        mat = (getattr(job, 'material', '') or '').strip().lower()
        grams = float(getattr(p, 'grams', 0) or 0)
        if mat == 'resin':
            resin_g += grams
        else:
            filament_g += grams
    
    # Queue age distribution (active jobs)
    now = datetime.now(timezone.utc)
    active_jobs = Job.query.filter(Job.status.in_(['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING'])).all()
    
    buckets = {'< 24h': 0, '1-2d': 0, '2-3d': 0, '3-7d': 0, '> 7d': 0}
    for job in active_jobs:
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        age_hours = (now - job.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600.0
        if age_hours < 24:
            buckets['< 24h'] += 1
        elif age_hours < 48:
            buckets['1-2d'] += 1
        elif age_hours < 72:
            buckets['2-3d'] += 1
        elif age_hours < 168:
            buckets['3-7d'] += 1
        else:
            buckets['> 7d'] += 1
    
    # Revenue over time
    revenue_counter = Counter()
    total_revenue_cents = 0
    payment_count = 0
    
    for p in payments:
        ts = getattr(p, 'paid_ts', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        # Apply filters by joining to Job lazily
        job = Job.query.get(p.job_id)
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        cents = int(getattr(p, 'price_cents', 0) or 0)
        total_revenue_cents += cents
        payment_count += 1
        revenue_counter[ts.date().isoformat()] += cents
    
    revenue_over_time = [{'date': d, 'cents': c} for d, c in sorted(revenue_counter.items())]
    avg_ticket_usd = round((total_revenue_cents / 100.0) / payment_count, 2) if payment_count else 0.0
    
    # Staff attribution for resources
    staff_printing = Counter()
    staff_payments = Counter()
    
    for e in printing_events:
        staff_printing[e.triggered_by] += 1
    
    for p in payments:
        staff_payments[p.paid_by_staff] += 1
    
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
        'staff_printing': dict(staff_printing),
        'staff_payments': dict(staff_payments),
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/financial', methods=['GET'])
@token_required
def financial():
    cache_key = ('financial', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
    printer_filter = request.args.get('printer')
    discipline_filter = request.args.get('discipline')
    
    # Revenue over time
    from collections import Counter
    revenue_counter = Counter()
    total_revenue_cents = 0
    payment_count = 0
    
    payments = Payment.query.filter(
        Payment.paid_ts >= start,
        Payment.paid_ts <= end
    ).all()
    
    for p in payments:
        ts = getattr(p, 'paid_ts', None)
        if not ts:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        # Apply filters by joining to Job lazily
        job = Job.query.get(p.job_id)
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        cents = int(getattr(p, 'price_cents', 0) or 0)
        total_revenue_cents += cents
        payment_count += 1
        revenue_counter[ts.date().isoformat()] += cents
    
    # Calculate estimated vs actual revenue
    estimated_revenue_cents = 0
    actual_revenue_cents = total_revenue_cents  # This is the actual revenue from payments
    
    # Get all jobs in the date range that have cost estimates
    jobs_with_estimates = Job.query.filter(
        Job.created_at >= start,
        Job.created_at <= end
    ).all()
    
    for job in jobs_with_estimates:
        # Apply filters
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        # Add estimated cost if available
        if job.cost_usd:
            estimated_revenue_cents += int(float(job.cost_usd) * 100)
    
    variance_cents = actual_revenue_cents - estimated_revenue_cents
    
    revenue_over_time = [{'date': d, 'cents': c} for d, c in sorted(revenue_counter.items())]
    avg_ticket_usd = round((total_revenue_cents / 100.0) / payment_count, 2) if payment_count else 0.0
    
    # Staff attribution for financial
    staff_revenue = Counter()
    for p in payments:
        job = Job.query.get(p.job_id)
        if printer_filter and getattr(job, 'printer', None) != printer_filter:
            continue
        if discipline_filter and getattr(job, 'discipline', None) != discipline_filter:
            continue
        
        cents = int(getattr(p, 'price_cents', 0) or 0)
        staff_revenue[p.paid_by_staff] += cents
    
    payload = {
        'total_revenue_cents': total_revenue_cents,
        'payment_count': payment_count,
        'avg_ticket_usd': avg_ticket_usd,
        'revenue_over_time': revenue_over_time,
        'staff_revenue': dict(staff_revenue),
        'estimated_revenue_cents': estimated_revenue_cents,
        'actual_revenue_cents': actual_revenue_cents,
        'variance_cents': variance_cents,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/events', methods=['GET'])
@token_required
def list_events():
    """Get all events with optional filtering"""
    # Get query parameters
    event_type = request.args.get('event_type')
    job_id = request.args.get('job_id')
    system_only = request.args.get('system_only', 'false').lower() == 'true'
    job_only = request.args.get('job_only', 'false').lower() == 'true'
    
    # Build query
    query = Event.query
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if job_id:
        query = query.filter(Event.job_id == job_id)
    
    if system_only:
        query = query.filter(Event.job_id.is_(None))
    
    if job_only:
        query = query.filter(Event.job_id.isnot(None))
    
    # Order by timestamp (newest first)
    events = query.order_by(Event.timestamp.desc()).all()
    
    return jsonify([e.to_dict() for e in events]), 200


# Staff Analytics Endpoints
@bp.route('/staff/overview', methods=['GET'])
@token_required
def staff_overview():
    """Get staff performance overview for the given date range"""
    cache_key = ('staff_overview', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
    # Get all active staff members
    active_staff = Staff.query.filter(Staff.is_active == True).all()
    staff_names = [staff.name for staff in active_staff]
    
    # Calculate performance metrics for each staff member
    staff_performance = {}
    
    for staff_name in staff_names:
        # Get all events by this staff member in the date range
        staff_events = Event.query.filter(
            Event.triggered_by == staff_name,
            Event.timestamp >= start,
            Event.timestamp <= end
        ).all()
        
        # Count different types of actions
        action_counts = {}
        for event in staff_events:
            event_type = event.event_type
            action_counts[event_type] = action_counts.get(event_type, 0) + 1
        
        # Calculate key metrics
        total_actions = len(staff_events)
        approvals = action_counts.get('StaffApproved', 0)
        rejections = action_counts.get('JobRejected', 0)
        completions = action_counts.get('JobMarkedComplete', 0)
        payments = action_counts.get('PaymentProcessed', 0)
        
        # Calculate response time (time from job creation to first staff action)
        response_times = []
        for event in staff_events:
            if event.event_type in ['StaffApproved', 'JobRejected']:
                # Find the job creation event
                job_created = Event.query.filter(
                    Event.job_id == event.job_id,
                    Event.event_type == 'JobCreated'
                ).first()
                
                if job_created:
                    job_created_time = job_created.timestamp
                    staff_action_time = event.timestamp
                    if job_created_time and staff_action_time:
                        if job_created_time.tzinfo is None:
                            job_created_time = job_created_time.replace(tzinfo=timezone.utc)
                        if staff_action_time.tzinfo is None:
                            staff_action_time = staff_action_time.replace(tzinfo=timezone.utc)
                        response_time_hours = (staff_action_time - job_created_time).total_seconds() / 3600.0
                        response_times.append(response_time_hours)
        
        avg_response_time = round(sum(response_times) / len(response_times), 2) if response_times else None
        
        # Calculate completion rate (approvals + rejections) / total jobs assigned
        total_assigned = approvals + rejections
        completion_rate = round((total_assigned / max(total_actions, 1)) * 100, 1) if total_actions > 0 else 0
        
        staff_performance[staff_name] = {
            'total_actions': total_actions,
            'approvals': approvals,
            'rejections': rejections,
            'completions': completions,
            'payments': payments,
            'avg_response_time_hours': avg_response_time,
            'completion_rate_percent': completion_rate,
            'action_breakdown': action_counts
        }
    
    # Calculate team-wide metrics
    total_team_actions = sum(perf['total_actions'] for perf in staff_performance.values())
    total_team_approvals = sum(perf['approvals'] for perf in staff_performance.values())
    total_team_rejections = sum(perf['rejections'] for perf in staff_performance.values())
    
    # Calculate workload distribution
    workload_distribution = {}
    for staff_name, perf in staff_performance.items():
        workload_percent = round((perf['total_actions'] / max(total_team_actions, 1)) * 100, 1)
        workload_distribution[staff_name] = workload_percent
    
    payload = {
        'staff_performance': staff_performance,
        'team_metrics': {
            'total_actions': total_team_actions,
            'total_approvals': total_team_approvals,
            'total_rejections': total_team_rejections,
            'active_staff_count': len(staff_names)
        },
        'workload_distribution': workload_distribution,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/staff/performance', methods=['GET'])
@token_required
def staff_performance():
    """Get detailed performance metrics for individual staff members"""
    cache_key = ('staff_performance', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    staff_name = request.args.get('staff')
    
    if not staff_name:
        return jsonify({'error': 'staff parameter is required'}), 400
    
    # Verify staff exists and is active
    staff = Staff.query.filter(Staff.name == staff_name, Staff.is_active == True).first()
    if not staff:
        return jsonify({'error': 'Staff member not found or inactive'}), 404
    
    # Get all events by this staff member in the date range
    staff_events = Event.query.filter(
        Event.triggered_by == staff_name,
        Event.timestamp >= start,
        Event.timestamp <= end
    ).order_by(Event.timestamp).all()
    
    # Group events by day for timeline
    from collections import defaultdict
    daily_activity = defaultdict(list)
    for event in staff_events:
        date_key = event.timestamp.date().isoformat()
        daily_activity[date_key].append({
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'job_id': event.job_id,
            'details': event.details
        })
    
    # Calculate performance trends
    performance_trends = []
    for date, events in sorted(daily_activity.items()):
        approvals = len([e for e in events if e['event_type'] == 'StaffApproved'])
        rejections = len([e for e in events if e['event_type'] == 'JobRejected'])
        completions = len([e for e in events if e['event_type'] == 'JobMarkedComplete'])
        
        performance_trends.append({
            'date': date,
            'total_actions': len(events),
            'approvals': approvals,
            'rejections': rejections,
            'completions': completions
        })
    
    # Calculate quality metrics
    total_approvals = len([e for e in staff_events if e.event_type == 'StaffApproved'])
    total_rejections = len([e for e in staff_events if e.event_type == 'JobRejected'])
    total_reviewed = total_approvals + total_rejections
    
    approval_rate = round((total_approvals / max(total_reviewed, 1)) * 100, 1) if total_reviewed > 0 else 0
    
    payload = {
        'staff_name': staff_name,
        'daily_activity': dict(daily_activity),
        'performance_trends': performance_trends,
        'quality_metrics': {
            'total_reviewed': total_reviewed,
            'approvals': total_approvals,
            'rejections': total_rejections,
            'approval_rate_percent': approval_rate
        },
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/staff/comparison', methods=['GET'])
@token_required
def staff_comparison():
    """Get comparison data between staff members"""
    cache_key = ('staff_comparison', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    # Parse date range
    start, end = _parse_date_range()
    
    # Get all active staff members
    active_staff = Staff.query.filter(Staff.is_active == True).all()
    staff_names = [staff.name for staff in active_staff]
    
    # Calculate comparison metrics
    comparison_data = {}
    
    for staff_name in staff_names:
        # Get events for this staff member
        staff_events = Event.query.filter(
            Event.triggered_by == staff_name,
            Event.timestamp >= start,
            Event.timestamp <= end
        ).all()
        
        # Calculate metrics
        total_actions = len(staff_events)
        approvals = len([e for e in staff_events if e.event_type == 'StaffApproved'])
        rejections = len([e for e in staff_events if e.event_type == 'JobRejected'])
        completions = len([e for e in staff_events if e.event_type == 'JobMarkedComplete'])
        
        # Calculate average response time
        response_times = []
        for event in staff_events:
            if event.event_type in ['StaffApproved', 'JobRejected']:
                job_created = Event.query.filter(
                    Event.job_id == event.job_id,
                    Event.event_type == 'JobCreated'
                ).first()
                
                if job_created:
                    job_created_time = job_created.timestamp
                    staff_action_time = event.timestamp
                    if job_created_time and staff_action_time:
                        if job_created_time.tzinfo is None:
                            job_created_time = job_created_time.replace(tzinfo=timezone.utc)
                        if staff_action_time.tzinfo is None:
                            staff_action_time = staff_action_time.replace(tzinfo=timezone.utc)
                        response_time_hours = (staff_action_time - job_created_time).total_seconds() / 3600.0
                        response_times.append(response_time_hours)
        
        avg_response_time = round(sum(response_times) / len(response_times), 2) if response_times else None
        
        comparison_data[staff_name] = {
            'total_actions': total_actions,
            'approvals': approvals,
            'rejections': rejections,
            'completions': completions,
            'avg_response_time_hours': avg_response_time,
            'productivity_score': total_actions,  # Simple productivity metric
            'quality_score': approvals - rejections if total_actions > 0 else 0  # Simple quality metric
        }
    
    # Calculate rankings
    productivity_ranking = sorted(staff_names, key=lambda x: comparison_data[x]['productivity_score'], reverse=True)
    quality_ranking = sorted(staff_names, key=lambda x: comparison_data[x]['quality_score'], reverse=True)
    
    payload = {
        'comparison_data': comparison_data,
        'rankings': {
            'productivity': productivity_ranking,
            'quality': quality_ranking
        },
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    
    _cache_set(cache_key, payload)
    return jsonify(payload), 200 

@bp.route('/student/overview', methods=['GET'])
@token_required
def student_overview():
    """Get student analytics overview for the given date range"""
    cache_key = ('student_overview', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    start, end = _parse_date_range()
    
    # Get unique students
    unique_students = Job.query.with_entities(Job.student_email).distinct().all()
    total_students = len(unique_students)
    
    # Get active students (submissions in date range)
    active_students_query = Job.query.filter(
        Job.created_at >= start,
        Job.created_at <= end
    ).with_entities(Job.student_email).distinct()
    active_students = len(active_students_query.all())
    
    # Calculate average jobs per student
    total_jobs = Job.query.count()
    avg_jobs_per_student = round(total_jobs / max(total_students, 1), 1)
    
    # Find most active student
    most_active_query = Job.query.with_entities(
        Job.student_name, 
        func.count().label('job_count')
    ).group_by(Job.student_name).order_by(func.count().desc()).first()
    
    most_active_student = most_active_query.student_name if most_active_query else "No data"
    
    payload = {
        'total_students': total_students,
        'active_students': active_students,
        'avg_jobs_per_student': avg_jobs_per_student,
        'most_active_student': most_active_student,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/student/performance', methods=['GET'])
@token_required
def student_performance():
    """Get student performance metrics for the given date range"""
    cache_key = ('student_performance', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    start, end = _parse_date_range()
    
    # Get approval rates by student
    student_approval_rates = {}
    student_job_counts = {}
    student_total_costs = {}
    
    jobs = Job.query.filter(
        Job.created_at >= start,
        Job.created_at <= end
    ).all()
    
    for job in jobs:
        student_email = job.student_email
        if student_email not in student_job_counts:
            student_job_counts[student_email] = 0
            student_total_costs[student_email] = 0
        
        student_job_counts[student_email] += 1
        if job.cost_usd:
            student_total_costs[student_email] += float(job.cost_usd)
        
        # Calculate approval rate
        if job.status in ['READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP']:
            if student_email not in student_approval_rates:
                student_approval_rates[student_email] = {'approved': 0, 'total': 0}
            student_approval_rates[student_email]['approved'] += 1
            student_approval_rates[student_email]['total'] += 1
        elif job.status == 'REJECTED':
            if student_email not in student_approval_rates:
                student_approval_rates[student_email] = {'approved': 0, 'total': 0}
            student_approval_rates[student_email]['total'] += 1
    
    # Calculate final approval rates
    final_approval_rates = {}
    for student_email, data in student_approval_rates.items():
        if data['total'] > 0:
            final_approval_rates[student_email] = round((data['approved'] / data['total']) * 100, 1)
        else:
            final_approval_rates[student_email] = 0
    
    # Calculate average costs
    avg_costs = {}
    for student_email, total_cost in student_total_costs.items():
        job_count = student_job_counts.get(student_email, 1)
        avg_costs[student_email] = round(total_cost / job_count, 2)
    
    payload = {
        'approval_rates': final_approval_rates,
        'avg_costs': avg_costs,
        'job_counts': student_job_counts,
        'total_costs': student_total_costs,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200


@bp.route('/student/trends', methods=['GET'])
@token_required
def student_trends():
    """Get student submission trends for the given date range"""
    cache_key = ('student_trends', tuple(sorted(request.args.items())))
    cached = _cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200
    
    start, end = _parse_date_range()
    
    # Get submissions by day
    daily_submissions = Job.query.with_entities(
        func.date(Job.created_at).label('date'),
        func.count().label('count')
    ).filter(
        Job.created_at >= start,
        Job.created_at <= end
    ).group_by(func.date(Job.created_at)).order_by(func.date(Job.created_at)).all()
    
    submissions_by_day = [
        {'date': str(row.date), 'count': row.count}
        for row in daily_submissions
    ]
    
    # Get submissions by discipline
    discipline_submissions = Job.query.with_entities(
        Job.discipline,
        func.count().label('count')
    ).filter(
        Job.created_at >= start,
        Job.created_at <= end
    ).group_by(Job.discipline).all()
    
    submissions_by_discipline = {
        row.discipline: row.count
        for row in discipline_submissions
    }
    
    payload = {
        'submissions_by_day': submissions_by_day,
        'submissions_by_discipline': submissions_by_discipline,
        'date_range': {
            'start': start.isoformat(),
            'end': end.isoformat()
        }
    }
    _cache_set(cache_key, payload)
    return jsonify(payload), 200 