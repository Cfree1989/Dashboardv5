from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import Counter
from sqlalchemy import func

from app import db
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment
from app.models.staff import Staff
from .analytics_service_interface import IAnalyticsService, DateRange, AnalyticsFilters
from app.business_logic.analytics.caching_service import CachingService
from app.utils.date_utils import DateUtils

class AnalyticsService(IAnalyticsService):
    """Analytics service implementation following roadmap patterns"""
    
    def __init__(self, caching_service=None):
        """Use dependency injection for testability"""
        self.cache = caching_service or CachingService()
    
    def get_overview_metrics(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get overview metrics for dashboard"""
        # Build cache key
        cache_key = ('overview', date_range.start.isoformat(), date_range.end.isoformat(), 
                    filters.printer, filters.discipline)
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Build query with filters
        q = Job.query
        if filters.printer:
            q = q.filter(Job.printer == filters.printer)
        if filters.discipline:
            q = q.filter(Job.discipline == filters.discipline)
        
        # Totals by status (queue view)
        rows = q.with_entities(Job.status, func.count()).group_by(Job.status).all()
        by_status = {status: int(count) for status, count in rows}
        active_statuses = {'UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING'}
        in_queue = sum(by_status.get(s, 0) for s in active_statuses)
        
        # Totals
        total_submissions = q.count()
        
        # Avg turnaround calculation
        avg_turnaround_hours = self._calculate_avg_turnaround(date_range, filters)
        
        # Recent rejections
        recent_rejections = self._count_recent_rejections(date_range, filters)
        
        payload = {
            'by_status': by_status,
            'in_queue': in_queue,
            'total_submissions': total_submissions,
            'avg_turnaround_hours': avg_turnaround_hours,
            'storage_usage_percent': None,  # Placeholder as per original
            'recent_rejections': recent_rejections,
            'date_range': {
                'start': date_range.start.isoformat(),
                'end': date_range.end.isoformat()
            }
        }
        
        # Cache result
        self.cache.set(cache_key, payload)
        return payload
    
    def get_trend_data(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get trend data over time"""
        cache_key = ('trends', date_range.start.isoformat(), date_range.end.isoformat(),
                    filters.printer, filters.discipline)
        
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Fetch events and bucket by date
        events = Event.query.filter(
            Event.event_type == 'JobCreated',
            Event.timestamp >= date_range.start,
            Event.timestamp <= date_range.end
        ).all()
        
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
            Event.timestamp >= date_range.start,
            Event.timestamp <= date_range.end
        ).all()
        
        for e in approvals:
            ts = getattr(e, 'timestamp', None)
            if not ts:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            # Apply filters if specified
            if filters.printer or filters.discipline:
                job = Job.query.get(e.job_id)
                if filters.printer and getattr(job, 'printer', None) != filters.printer:
                    continue
                if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                    continue
            
            approvals_bucket[ts.date().isoformat()] += 1
        
        approvals_series = [{'date': d, 'count': c} for d, c in sorted(approvals_bucket.items())]
        
        payload = {
            'submissions': series,
            'approvals': approvals_series,
            'date_range': {
                'start': date_range.start.isoformat(),
                'end': date_range.end.isoformat()
            }
        }
        
        self.cache.set(cache_key, payload)
        return payload
    
    def get_resource_metrics(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        cache_key = ('resources', date_range.start.isoformat(), date_range.end.isoformat(),
                    filters.printer, filters.discipline)
        
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Build base query with filters
        q = Job.query.filter(
            Job.created_at >= date_range.start,
            Job.created_at <= date_range.end
        )
        
        if filters.printer:
            q = q.filter(Job.printer == filters.printer)
        if filters.discipline:
            q = q.filter(Job.discipline == filters.discipline)
        
        jobs = q.all()
        
        # Calculate metrics
        printing_throughput = len([j for j in jobs if j.status in ['PRINTING', 'COMPLETED', 'PAIDPICKEDUP']])
        
        # Average lead time calculation
        lead_times = []
        for job in jobs:
            if job.status in ['COMPLETED', 'PAIDPICKEDUP']:
                created_event = Event.query.filter(
                    Event.job_id == job.id,
                    Event.event_type == 'JobCreated'
                ).first()
                completed_event = Event.query.filter(
                    Event.job_id == job.id,
                    Event.event_type == 'JobMarkedComplete'
                ).first()
                
                if created_event and completed_event:
                    created_time = created_event.timestamp
                    completed_time = completed_event.timestamp
                    if created_time and completed_time:
                        if created_time.tzinfo is None:
                            created_time = created_time.replace(tzinfo=timezone.utc)
                        if completed_time.tzinfo is None:
                            completed_time = completed_time.replace(tzinfo=timezone.utc)
                        lead_time_hours = (completed_time - created_time).total_seconds() / 3600.0
                        lead_times.append(lead_time_hours)
        
        average_lead_time = round(sum(lead_times) / len(lead_times), 2) if lead_times else None
        
        # Printer utilization
        printer_counts = Counter()
        for job in jobs:
            if job.printer:
                printer_counts[job.printer] += 1
        
        printer_utilization = dict(printer_counts)
        
        # Material consumption should be based on Payments within the date window
        # Sum grams by material using Payment.paid_ts and associated Job.material
        filament_g = 0.0
        resin_g = 0.0
        payments_in_range = Payment.query.filter(
            Payment.paid_ts >= date_range.start,
            Payment.paid_ts <= date_range.end
        ).all()
        for p in payments_in_range:
            job = Job.query.get(p.job_id)
            if not job:
                continue
            # Apply filters if specified
            if filters.printer and getattr(job, 'printer', None) != filters.printer:
                continue
            if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                continue
            mat = (getattr(job, 'material', None) or 'filament').strip().lower()
            grams = float(getattr(p, 'grams', 0) or 0)
            if mat == 'resin':
                resin_g += grams
            else:
                filament_g += grams
        
        # Queue age buckets
        buckets = self._calculate_queue_age_buckets(jobs)
        
        # Revenue data
        revenue_data = self._calculate_revenue_metrics(date_range, filters)
        
        payload = {
            'printing_throughput': printing_throughput,
            'average_lead_time': average_lead_time,
            'printer_utilization': printer_utilization,
            'material_consumption_g': {'filament': filament_g, 'resin': resin_g},
            'queue_age_buckets': buckets,
            **revenue_data,
            'date_range': {
                'start': date_range.start.isoformat(),
                'end': date_range.end.isoformat()
            }
        }
        
        self.cache.set(cache_key, payload)
        return payload
    
    def get_financial_summary(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get financial analysis data"""
        cache_key = ('financial', date_range.start.isoformat(), date_range.end.isoformat(),
                    filters.printer, filters.discipline)
        
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Revenue over time
        revenue_counter = Counter()
        total_revenue_cents = 0
        payment_count = 0
        
        payments = Payment.query.filter(
            Payment.paid_ts >= date_range.start,
            Payment.paid_ts <= date_range.end
        ).all()
        
        for p in payments:
            ts = getattr(p, 'paid_ts', None)
            if not ts:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            # Apply filters by joining to Job
            job = Job.query.get(p.job_id)
            if filters.printer and getattr(job, 'printer', None) != filters.printer:
                continue
            if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                continue
            
            cents = int(getattr(p, 'price_cents', 0) or 0)
            total_revenue_cents += cents
            payment_count += 1
            revenue_counter[ts.date().isoformat()] += cents
        
        # Calculate estimated vs actual revenue
        estimated_revenue_cents = 0
        actual_revenue_cents = total_revenue_cents
        
        # Get all jobs in the date range that have cost estimates
        jobs_with_estimates = Job.query.filter(
            Job.created_at >= date_range.start,
            Job.created_at <= date_range.end
        ).all()
        
        for job in jobs_with_estimates:
            # Apply filters
            if filters.printer and getattr(job, 'printer', None) != filters.printer:
                continue
            if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                continue
            
            # Add estimated cost if available
            if job.cost_usd:
                estimated_revenue_cents += int(float(job.cost_usd) * 100)
        
        variance_cents = actual_revenue_cents - estimated_revenue_cents
        
        revenue_over_time = [{'date': d, 'cents': c} for d, c in sorted(revenue_counter.items())]
        avg_ticket_usd = round((total_revenue_cents / 100.0) / payment_count, 2) if payment_count else 0.0
        
        payload = {
            'revenue_over_time': revenue_over_time,
            'total_revenue_cents': total_revenue_cents,
            'estimated_revenue_cents': estimated_revenue_cents,
            'variance_cents': variance_cents,
            'avg_ticket_usd': avg_ticket_usd,
            'payment_count': payment_count,
            'date_range': {
                'start': date_range.start.isoformat(),
                'end': date_range.end.isoformat()
            }
        }
        
        self.cache.set(cache_key, payload)
        return payload
    
    def _calculate_avg_turnaround(self, date_range: DateRange, filters: AnalyticsFilters) -> Optional[float]:
        """Calculate average turnaround time for completed jobs"""
        completed_events = Event.query.filter(
            Event.event_type == 'JobMarkedComplete',
            Event.timestamp >= date_range.start,
            Event.timestamp <= date_range.end
        ).all()
        
        diffs: List[float] = []
        created_by_job: Dict[str, datetime] = {}
        
        # Build lookup of first JobCreated event per job
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
        
        return round(sum(diffs) / len(diffs), 2) if diffs else None
    
    def _count_recent_rejections(self, date_range: DateRange, filters: AnalyticsFilters) -> int:
        """Count recent rejections in date range respecting filters"""
        rej_q = Event.query.filter(
            Event.event_type == 'JobRejected',
            Event.timestamp >= date_range.start,
            Event.timestamp <= date_range.end
        )
        
        recent_rejections = 0
        for e in rej_q.all():
            if filters.printer or filters.discipline:
                j = Job.query.get(e.job_id)
                if filters.printer and getattr(j, 'printer', None) != filters.printer:
                    continue
                if filters.discipline and getattr(j, 'discipline', None) != filters.discipline:
                    continue
            recent_rejections += 1
        
        return recent_rejections
    
    def _calculate_queue_age_buckets(self, jobs: List[Job]) -> Dict[str, int]:
        """Calculate queue age distribution buckets"""
        buckets = {'0-24h': 0, '1-3d': 0, '3-7d': 0, '1-2w': 0, '2w+': 0}
        now = datetime.now(timezone.utc)
        
        for job in jobs:
            if job.status in ['UPLOADED', 'PENDING', 'READYTOPRINT']:
                created_time = job.created_at
                if created_time.tzinfo is None:
                    created_time = created_time.replace(tzinfo=timezone.utc)
                
                age_hours = (now - created_time).total_seconds() / 3600.0
                
                if age_hours <= 24:
                    buckets['0-24h'] += 1
                elif age_hours <= 72:
                    buckets['1-3d'] += 1
                elif age_hours <= 168:
                    buckets['3-7d'] += 1
                elif age_hours <= 336:
                    buckets['1-2w'] += 1
                else:
                    buckets['2w+'] += 1
        
        return buckets
    
    def _calculate_revenue_metrics(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Calculate revenue-related metrics"""
        payments = Payment.query.filter(
            Payment.paid_ts >= date_range.start,
            Payment.paid_ts <= date_range.end
        ).all()
        
        revenue_counter = Counter()
        total_revenue_cents = 0
        payment_count = 0
        
        for p in payments:
            ts = getattr(p, 'paid_ts', None)
            if not ts:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            
            # Apply filters
            job = Job.query.get(p.job_id)
            if filters.printer and getattr(job, 'printer', None) != filters.printer:
                continue
            if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                continue
            
            cents = int(getattr(p, 'price_cents', 0) or 0)
            total_revenue_cents += cents
            payment_count += 1
            revenue_counter[ts.date().isoformat()] += cents
        
        revenue_over_time = [{'date': d, 'cents': c} for d, c in sorted(revenue_counter.items())]
        avg_ticket_usd = round((total_revenue_cents / 100.0) / payment_count, 2) if payment_count else 0.0
        
        # Staff attribution
        staff_printing = Counter()
        staff_payments = Counter()
        
        for p in payments:
            job = Job.query.get(p.job_id)
            if filters.printer and getattr(job, 'printer', None) != filters.printer:
                continue
            if filters.discipline and getattr(job, 'discipline', None) != filters.discipline:
                continue
            
            if p.paid_by_staff:
                staff_payments[p.paid_by_staff] += 1
        
        return {
            'revenue_over_time': revenue_over_time,
            'total_revenue_cents': total_revenue_cents,
            'avg_ticket_usd': avg_ticket_usd,
            'payment_count': payment_count,
            'staff_payments': dict(staff_payments)
        }
