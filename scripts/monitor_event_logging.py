#!/usr/bin/env python3
"""
Event Logging System Production Monitoring Script

This script provides monitoring capabilities for the event logging system
in production. It includes:

1. Event statistics and health checks
2. Performance monitoring
3. Error detection and reporting
4. System-level event tracking
5. Database integrity checks
"""

import os
import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app, db
from app.models.event import Event
from app.services.event_service import JOB_SPECIFIC_EVENTS, SYSTEM_EVENTS


def get_event_statistics():
    """Get comprehensive event statistics."""
    stats = {
        'total_events': Event.query.count(),
        'system_events': Event.query.filter(Event.job_id.is_(None)).count(),
        'job_events': Event.query.filter(Event.job_id.isnot(None)).count(),
        'events_today': Event.query.filter(
            Event.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        'events_this_hour': Event.query.filter(
            Event.timestamp >= datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        ).count(),
        'unique_event_types': len(set([e.event_type for e in Event.query.all()])),
        'latest_event': None,
        'oldest_event': None
    }
    
    # Get latest and oldest events
    latest_event = Event.query.order_by(Event.timestamp.desc()).first()
    oldest_event = Event.query.order_by(Event.timestamp.asc()).first()
    
    if latest_event:
        stats['latest_event'] = {
            'timestamp': latest_event.timestamp.isoformat(),
            'event_type': latest_event.event_type,
            'triggered_by': latest_event.triggered_by
        }
    
    if oldest_event:
        stats['oldest_event'] = {
            'timestamp': oldest_event.timestamp.isoformat(),
            'event_type': oldest_event.event_type,
            'triggered_by': oldest_event.triggered_by
        }
    
    return stats


def get_event_type_breakdown():
    """Get breakdown of events by type."""
    events = Event.query.all()
    breakdown = defaultdict(int)
    
    for event in events:
        breakdown[event.event_type] += 1
    
    return dict(breakdown)


def get_recent_activity(hours=24):
    """Get recent activity summary."""
    since = datetime.utcnow() - timedelta(hours=hours)
    recent_events = Event.query.filter(Event.timestamp >= since).all()
    
    activity = {
        'total_recent': len(recent_events),
        'system_events': len([e for e in recent_events if e.job_id is None]),
        'job_events': len([e for e in recent_events if e.job_id is not None]),
        'by_type': defaultdict(int),
        'by_user': defaultdict(int)
    }
    
    for event in recent_events:
        activity['by_type'][event.event_type] += 1
        activity['by_user'][event.triggered_by] += 1
    
    activity['by_type'] = dict(activity['by_type'])
    activity['by_user'] = dict(activity['by_user'])
    
    return activity


def check_database_integrity():
    """Check database integrity for events."""
    issues = []
    
    # Check for events with invalid event types
    all_event_types = JOB_SPECIFIC_EVENTS.union(SYSTEM_EVENTS)
    invalid_events = Event.query.filter(~Event.event_type.in_(all_event_types)).all()
    
    if invalid_events:
        issues.append(f"Found {len(invalid_events)} events with invalid event types")
    
    # Check for job-specific events without job_id
    job_events_without_id = Event.query.filter(
        Event.event_type.in_(JOB_SPECIFIC_EVENTS),
        Event.job_id.is_(None)
    ).all()
    
    if job_events_without_id:
        issues.append(f"Found {len(job_events_without_id)} job-specific events without job_id")
    
    # Check for system events with job_id
    system_events_with_id = Event.query.filter(
        Event.event_type.in_(SYSTEM_EVENTS),
        Event.job_id.isnot(None)
    ).all()
    
    if system_events_with_id:
        issues.append(f"Found {len(system_events_with_id)} system events with job_id")
    
    # Check for events with missing required fields
    null_triggered_by = Event.query.filter(Event.triggered_by.is_(None)).count()
    if null_triggered_by > 0:
        issues.append(f"Found {null_triggered_by} events with null triggered_by")
    
    null_workstation_id = Event.query.filter(Event.workstation_id.is_(None)).count()
    if null_workstation_id > 0:
        issues.append(f"Found {null_workstation_id} events with null workstation_id")
    
    return issues


def performance_test():
    """Run a quick performance test."""
    start_time = time.time()
    
    # Test query performance
    Event.query.count()
    Event.query.filter(Event.job_id.is_(None)).count()
    Event.query.filter(Event.job_id.isnot(None)).count()
    
    query_time = time.time() - start_time
    
    return {
        'query_time_seconds': query_time,
        'status': 'healthy' if query_time < 1.0 else 'slow'
    }


def generate_report():
    """Generate a comprehensive monitoring report."""
    print("📊 Event Logging System Production Monitoring Report")
    print("=" * 60)
    print(f"Generated at: {datetime.now().isoformat()}")
    print()
    
    # Get statistics
    stats = get_event_statistics()
    breakdown = get_event_type_breakdown()
    activity = get_recent_activity()
    integrity_issues = check_database_integrity()
    performance = performance_test()
    
    # Print statistics
    print("📈 Event Statistics:")
    print(f"   - Total events: {stats['total_events']:,}")
    print(f"   - System events: {stats['system_events']:,}")
    print(f"   - Job events: {stats['job_events']:,}")
    print(f"   - Events today: {stats['events_today']:,}")
    print(f"   - Events this hour: {stats['events_this_hour']:,}")
    print(f"   - Unique event types: {stats['unique_event_types']}")
    print()
    
    # Print recent activity
    print("🕒 Recent Activity (Last 24 Hours):")
    print(f"   - Total events: {activity['total_recent']:,}")
    print(f"   - System events: {activity['system_events']:,}")
    print(f"   - Job events: {activity['job_events']:,}")
    print()
    
    if activity['by_type']:
        print("   Event Types:")
        for event_type, count in sorted(activity['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"     - {event_type}: {count}")
        print()
    
    if activity['by_user']:
        print("   Active Users:")
        for user, count in sorted(activity['by_user'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     - {user}: {count}")
        print()
    
    # Print event type breakdown
    print("📋 Event Type Breakdown:")
    for event_type, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['total_events']) * 100 if stats['total_events'] > 0 else 0
        print(f"   - {event_type}: {count:,} ({percentage:.1f}%)")
    print()
    
    # Print integrity check results
    print("🔍 Database Integrity Check:")
    if integrity_issues:
        print("   ❌ Issues found:")
        for issue in integrity_issues:
            print(f"     - {issue}")
    else:
        print("   ✅ No integrity issues found")
    print()
    
    # Print performance results
    print("⚡ Performance Check:")
    print(f"   - Query time: {performance['query_time_seconds']:.3f}s")
    print(f"   - Status: {performance['status']}")
    print()
    
    # Print latest event info
    if stats['latest_event']:
        print("🕐 Latest Event:")
        latest = stats['latest_event']
        print(f"   - Time: {latest['timestamp']}")
        print(f"   - Type: {latest['event_type']}")
        print(f"   - User: {latest['triggered_by']}")
        print()
    
    # Print overall health status
    print("🏥 Overall Health Status:")
    health_score = 100
    
    if integrity_issues:
        health_score -= len(integrity_issues) * 20
    
    if performance['status'] == 'slow':
        health_score -= 20
    
    if stats['events_this_hour'] == 0:
        health_score -= 10  # No recent activity
    
    if health_score >= 90:
        status = "🟢 EXCELLENT"
    elif health_score >= 70:
        status = "🟡 GOOD"
    elif health_score >= 50:
        status = "🟠 FAIR"
    else:
        status = "🔴 POOR"
    
    print(f"   - Health Score: {health_score}/100")
    print(f"   - Status: {status}")
    print()
    
    print("🏁 Monitoring report completed")


def main():
    """Main monitoring function."""
    try:
        # Set up the application context
        app = create_app()
        with app.app_context():
            # Create database tables if they don't exist
            db.create_all()
            generate_report()
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
