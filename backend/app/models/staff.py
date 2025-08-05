from app import db
from datetime import datetime

class Staff(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'name': self.name,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None
        } 