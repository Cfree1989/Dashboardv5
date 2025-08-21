from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from app import db
from app.models.job import Job
from app.models.payment import Payment
from app.models.event import Event
from app.business_logic.shared_services.validation_service import ValidationService
from app.services.infrastructure.file_service import move_authoritative
from app.services.infrastructure.payment_service_interface import IPaymentService, PaymentData

class PaymentService(IPaymentService):
    def __init__(self, validation_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
    
    def _get_workstation_id(self):
        """Get workstation ID safely for Flask context compatibility"""
        try:
            from flask import g
            return getattr(g, 'workstation_id', None)
        except (ImportError, RuntimeError):
            # Outside Flask context (e.g., in tests)
            return None
    
    def record_payment(self, job_id: str, payment_data: PaymentData) -> Payment:
        """Record payment and transition job to PAIDPICKEDUP"""
        # Validate job exists and is in correct status
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'COMPLETED':
            raise ValueError('Job must be in COMPLETED to record payment')
        
        # Validate staff
        staff_result = self.validation.validate_staff(payment_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate payment data
        if payment_data.grams <= 0:
            raise ValueError('grams must be greater than 0')
        if not payment_data.txn_no.strip():
            raise ValueError('txn_no is required')
        if not payment_data.picked_up_by.strip():
            raise ValueError('picked_up_by is required')
        
        # Calculate final cost
        price_cents = self.calculate_final_cost(job.material, payment_data.grams)
        
        # Create payment record
        payment = Payment(
            job_id=job.id,
            grams=payment_data.grams,
            price_cents=price_cents,
            txn_no=payment_data.txn_no,
            picked_up_by=payment_data.picked_up_by,
            paid_by_staff=payment_data.staff_name,
        )
        db.session.add(payment)
        
        # Transition job to PAIDPICKEDUP
        job.status = 'PAIDPICKEDUP'
        job.last_updated_by = payment_data.staff_name
        move_authoritative(job, 'PAIDPICKEDUP')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        self._log_payment_event(job, price_cents, payment_data.staff_name)
        
        return payment
    
    def calculate_final_cost(self, material: str, grams: float) -> int:
        """Calculate final cost in cents"""
        material_rate = 0.20 if (material or '').lower() == 'resin' else 0.10
        raw_cost = grams * material_rate
        final_cost = max(3.0, raw_cost)  # $3.00 minimum charge
        
        cost_decimal = Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return int(cost_decimal * 100)
    
    def _log_payment_event(self, job: Job, price_cents: int, staff_name: str):
        """Log payment event with workstation attribution"""
        workstation_id = self._get_workstation_id()
        evt = Event(
            job_id=job.id, 
            event_type='PaymentRecorded', 
            details={'price_cents': price_cents}, 
            triggered_by=staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'PaymentRecorded')
    
    def _sync_authoritative_metadata(self, job: Job, filename: str, staff_name: str, event_type: str):
        """Sync authoritative metadata after payment"""
        try:
            from app.services.file_service import _sync_authoritative_metadata
            _sync_authoritative_metadata(job, filename, staff_name, event_type)
        except ImportError:
            # Fallback if file service not available
            pass
