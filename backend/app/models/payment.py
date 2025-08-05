from app import db
from datetime import datetime

class Payment(db.Model):
    job_id = db.Column(db.String, db.ForeignKey('job.id'), primary_key=True)
    grams = db.Column(db.Float, nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    txn_no = db.Column(db.String(50), nullable=False)
    picked_up_by = db.Column(db.String(100), nullable=False)
    paid_ts = db.Column(db.DateTime, default=datetime.utcnow)
    paid_by_staff = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'grams': self.grams,
            'price_cents': self.price_cents,
            'price_usd': self.price_cents / 100.0,
            'txn_no': self.txn_no,
            'picked_up_by': self.picked_up_by,
            'paid_ts': self.paid_ts.isoformat(),
            'paid_by_staff': self.paid_by_staff
        } 