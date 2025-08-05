from app import db
from datetime import datetime

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String, db.ForeignKey('job.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    triggered_by = db.Column(db.String(100), nullable=False)
    workstation_id = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'details': self.details,
            'triggered_by': self.triggered_by,
            'workstation_id': self.workstation_id
        } 