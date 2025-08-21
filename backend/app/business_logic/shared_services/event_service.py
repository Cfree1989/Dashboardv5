from app import db
from app.models.event import Event
from flask import g

# Event type classification for validation
JOB_SPECIFIC_EVENTS = {
    'JobCreated', 'JobApproved', 'JobRejected', 'JobConfirmed', 
    'JobStarted', 'JobCompleted', 'JobPaid', 'JobArchived', 'JobDeleted',
    'StudentConfirmed', 'ResendConfirmationRequested', 'ApprovalEmailResent',
    'AuditIssueReviewed', 'AuditMetadataRepaired', 'AuditLocationRepaired', 'AuditFileRelinked'
}

SYSTEM_EVENTS = {
    'AllJobsDeleted', 'MockJobsGenerated', 'CatalogUpdated', 
    'ErrorMonitoringCleared', 'AdminAction', 'SystemMaintenance',
    'OrphanedFileDeleted', 'StaleFileDeleted', 'CatalogSeeded'
}

def log_event(event_type, details=None, triggered_by=None, workstation_id=None, job_id=None):
    """
    Log an event to the database.
    
    Args:
        event_type: Type of event (must be in JOB_SPECIFIC_EVENTS or SYSTEM_EVENTS)
        details: Optional JSON details about the event
        triggered_by: Who triggered the event (defaults to workstation_id from g)
        workstation_id: Workstation ID (defaults to workstation_id from g)
        job_id: Job ID for job-specific events, None for system events
    
    Raises:
        ValueError: If job_id is required but not provided, or if event_type is invalid
    """
    # Validate event type
    if event_type not in JOB_SPECIFIC_EVENTS and event_type not in SYSTEM_EVENTS:
        raise ValueError(f"Invalid event type: {event_type}")
    
    # Validate job_id for job-specific events
    if event_type in JOB_SPECIFIC_EVENTS and job_id is None:
        raise ValueError(f"job_id is required for job-specific event type: {event_type}")
    
    # Validate job_id for system events (should be None)
    if event_type in SYSTEM_EVENTS and job_id is not None:
        raise ValueError(f"job_id should be None for system event type: {event_type}")
    
    evt = Event(
        job_id=job_id,  # Can now be None for system events
        event_type=event_type,
        details=details or {},
        triggered_by=triggered_by or getattr(g, 'workstation_id', 'system'),
        workstation_id=workstation_id or getattr(g, 'workstation_id', 'system')
    )
    db.session.add(evt)
    db.session.commit()