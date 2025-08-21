from typing import Optional

# Import foundation services
from app.services.validation_service import ValidationService
from app.services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app import db

class JobNoteData:
    """Data class for job note parameters"""
    def __init__(self, staff_name: str, text: str):
        self.staff_name = staff_name
        self.text = text

class JobUpdateNotesData:
    """Data class for updating notes parameters"""
    def __init__(self, staff_name: str, notes: str):
        self.staff_name = staff_name
        self.notes = notes

class JobNotesService:
    """Service for managing job notes operations"""
    
    def __init__(self, validation_service=None, response_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
        self.response = response_service or ResponseService
    
    def _get_workstation_id(self) -> Optional[str]:
        """Get workstation ID from request context if available"""
        try:
            from flask import request
            return request.headers.get('X-Workstation-ID')
        except RuntimeError:
            # Not in request context (e.g., during testing)
            return None
    
    def append_note(self, job_id: str, note_data: JobNoteData, workstation_id: str = None) -> Job:
        """Append a note to a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        staff_result = self.validation.validate_staff(note_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate text
        if not isinstance(note_data.text, str):
            raise ValueError('text must be a string')
        
        text = note_data.text.strip()
        if not text:
            raise ValueError('text is required')
        
        # Validate length limits
        per_entry_limit = 1000
        total_limit = 5000
        if len(text) > per_entry_limit:
            raise ValueError(f'text must be at most {per_entry_limit} characters')
        
        job = job_result.data
        
        # Build the new line to append
        new_line = f"{note_data.staff_name} - {text}"
        current = job.notes or ''
        # Compute resulting total length with newline if needed
        separator = ('\n' if current else '')
        proposed = current + separator + new_line
        if len(proposed) > total_limit:
            raise ValueError('total notes length exceeded')
        
        # Update job
        job.notes = proposed
        job.last_updated_by = note_data.staff_name
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type='NoteAdded',
            details={'text_len': len(text)},
            triggered_by=note_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return job
    
    def update_notes(self, job_id: str, notes_data: JobUpdateNotesData, workstation_id: str = None) -> Job:
        """Update job notes with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        staff_result = self.validation.validate_staff(notes_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate notes
        if not isinstance(notes_data.notes, str):
            raise ValueError('notes must be a string')
        
        if len(notes_data.notes) > 5000:
            raise ValueError('notes must be at most 5000 characters')
        
        job = job_result.data
        
        # Update job
        job.notes = notes_data.notes
        job.last_updated_by = notes_data.staff_name
        db.session.add(job)
        db.session.commit()
        
        # Log event with length only (avoid storing full notes in event log)
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type='NotesUpdated',
            details={'notes_len': len(notes_data.notes)},
            triggered_by=notes_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return job
