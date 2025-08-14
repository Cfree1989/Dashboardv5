from app import db
from app.models.event import Event
from flask import g

def log_event(event_type, details=None, triggered_by=None, workstation_id=None, job_id=None):
    evt = Event(
        job_id=job_id,
        event_type=event_type,
        details=details or {},
        triggered_by=triggered_by or getattr(g, 'workstation_id', 'system'),
        workstation_id=workstation_id or getattr(g, 'workstation_id', 'system')
    )
    db.session.add(evt)
    db.session.commit()