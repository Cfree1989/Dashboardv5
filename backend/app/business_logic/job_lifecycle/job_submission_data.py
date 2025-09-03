"""
Data classes for job submission operations
"""

from typing import Optional
from werkzeug.datastructures import FileStorage


class JobSubmissionData:
    """Data class for job submission parameters"""
    def __init__(self, 
                 student_name: str,
                 student_email: str,
                 discipline: str,
                 class_number: str,
                 printer: str,
                 color: str,
                 material: str,
                 file: FileStorage,
                 file_hash: str,
                 display_name: str,
                 metadata: dict):
        self.student_name = student_name
        self.student_email = student_email
        self.discipline = discipline
        self.class_number = class_number
        self.printer = printer
        self.color = color
        self.material = material
        self.file = file
        self.file_hash = file_hash
        self.display_name = display_name
        self.metadata = metadata


class JobConfirmationData:
    """Data class for job confirmation parameters"""
    def __init__(self, token: str):
        self.token = token


class JobResendConfirmationData:
    """Data class for resending confirmation email parameters"""  
    def __init__(self, job_id: Optional[str] = None, token: Optional[str] = None):
        self.job_id = job_id
        self.token = token
