# backend/app/services/validation_service.py
# LESSON: Services must work in both web and test contexts
from typing import Optional

class ValidationResult:
    def __init__(self, is_valid: bool, error_message: Optional[str] = None, data=None):
        self.is_valid = is_valid
        self.error_message = error_message
        self.data = data

class ValidationService:
    @staticmethod
    def validate_staff(staff_name: str) -> ValidationResult:
        """Validates staff exists and is active"""
        if not staff_name or not staff_name.strip():
            return ValidationResult(False, 'staff_name is required')

        # Lazy import to avoid import-time side effects
        from app.models.staff import Staff
        staff = Staff.query.get(staff_name.strip())
        if not staff or not staff.is_active:
            return ValidationResult(False, 'Invalid or inactive staff_name')

        return ValidationResult(True, data=staff)

    @staticmethod
    def validate_job_exists(job_id: str) -> ValidationResult:
        """Validates job exists and is accessible"""
        from app.models.job import Job
        try:
            job = Job.query.get(job_id)
        except RuntimeError:
            # Outside Flask context: treat as not found
            return ValidationResult(False, 'Job not found')
        if not job:
            return ValidationResult(False, 'Job not found')
        return ValidationResult(True, data=job)

    @staticmethod
    def validate_status_transition(from_status: str, to_status: str) -> ValidationResult:
        """Validates if status transition is allowed"""
        valid_transitions = {
            'UPLOADED': ['PENDING', 'REJECTED', 'ARCHIVED'],
            'PENDING': ['READYTOPRINT', 'REJECTED'],
            'READYTOPRINT': ['PRINTING'],
            'PRINTING': ['COMPLETED', 'READYTOPRINT'],
            'COMPLETED': ['PAIDPICKEDUP', 'PRINTING'],
            'PAIDPICKEDUP': ['COMPLETED']
        }

        if from_status not in valid_transitions:
            return ValidationResult(False, f'Invalid source status: {from_status}')
        if to_status not in valid_transitions[from_status]:
            return ValidationResult(False, f'Invalid transition from {from_status} to {to_status}')

        return ValidationResult(True)
