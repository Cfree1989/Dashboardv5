from app import db
from datetime import datetime, timezone
import uuid

class Job(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
    short_id = db.Column(db.String(12), unique=True, index=True, nullable=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_email = db.Column(db.String(100), nullable=False)
    discipline = db.Column(db.String(50), nullable=False)
    class_number = db.Column(db.String(50), nullable=False)
    
    # File Management
    original_filename = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    metadata_path = db.Column(db.String(512), nullable=False)
    file_hash = db.Column(db.String(64), nullable=True)
    
    # Job Configuration
    status = db.Column(db.String(50), default='UPLOADED')
    printer = db.Column(db.String(64), nullable=False)
    color = db.Column(db.String(32), nullable=False)
    material = db.Column(db.String(32), nullable=False)
    weight_g = db.Column(db.Float, nullable=True)
    time_hours = db.Column(db.Float, nullable=True)
    cost_usd = db.Column(db.Numeric(6, 2), nullable=True)
    
    # Student Confirmation
    acknowledged_minimum_charge = db.Column(db.Boolean, default=False)
    student_confirmed = db.Column(db.Boolean, default=False)
    student_confirmed_at = db.Column(db.DateTime, nullable=True)
    confirm_token = db.Column(db.String(128), nullable=True, unique=True)
    confirm_token_expires = db.Column(db.DateTime, nullable=True)
    is_confirmation_expired = db.Column(db.Boolean, default=False)
    confirmation_last_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Staff Management
    reject_reasons = db.Column(db.JSON, nullable=True)
    staff_viewed_at = db.Column(db.DateTime, nullable=True)
    last_updated_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='job', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='job', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'short_id': self.short_id,
            'student_name': self.student_name,
            'student_email': self.student_email,
            'discipline': self.discipline,
            'class_number': self.class_number,
            'original_filename': self.original_filename,
            'display_name': self.display_name,
            'status': self.status,
            'printer': self.printer,
            'color': self.color,
            'material': self.material,
            'weight_g': float(self.weight_g) if self.weight_g else None,
            'time_hours': float(self.time_hours) if self.time_hours else None,
            'cost_usd': float(self.cost_usd) if self.cost_usd else None,
            'staff_viewed_at': (
                self.staff_viewed_at.replace(tzinfo=timezone.utc).isoformat() if self.staff_viewed_at else None
            ),
            'student_confirmed': self.student_confirmed,
            'student_confirmed_at': (
                self.student_confirmed_at.replace(tzinfo=timezone.utc).isoformat() if self.student_confirmed_at else None
            ),
            'is_confirmation_expired': self.is_confirmation_expired,
            'reject_reasons': self.reject_reasons,
            'last_updated_by': self.last_updated_by,
            'notes': self.notes,
            'created_at': self.created_at.replace(tzinfo=timezone.utc).isoformat(),
            'updated_at': self.updated_at.replace(tzinfo=timezone.utc).isoformat()
        } 