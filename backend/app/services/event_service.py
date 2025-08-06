from app import db
from app.models.event import Event
from flask import g

def log_event(job_id, event_type, details=None):
    evt = Event(
        job_id=job_id,
        event_type=event_type,
        details=details or {},
        triggered_by=getattr(g, 'workstation_id', 'system'),
        workstation_id=getattr(g, 'workstation_id', 'system')
    )
    db.session.add(evt)
    db.session.commit()