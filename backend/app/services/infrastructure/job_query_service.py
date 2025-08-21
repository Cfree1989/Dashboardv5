"""
Job Query Service

Handles job querying and filtering logic extracted from list_jobs and get_job_counts routes.
Extracted for Phase 3 route simplification.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import func, or_
from app.models.job import Job


class JobFilters:
    """Filter parameters for job queries"""
    def __init__(self, status: Optional[str] = None, search: Optional[str] = None, 
                 printer: Optional[str] = None, discipline: Optional[str] = None):
        self.status = status
        self.search = search
        self.printer = printer
        self.discipline = discipline


class JobQueryService:
    """Service for querying and filtering jobs"""
    
    def list_jobs(self, filters: JobFilters) -> List[Job]:
        """
        Get filtered list of jobs
        
        Args:
            filters: JobFilters object with filtering criteria
            
        Returns:
            List of Job objects matching the filters
        """
        query = Job.query
        
        # Apply database-level filters
        if filters.status:
            query = query.filter_by(status=filters.status)
        
        if filters.printer:
            query = query.filter_by(printer=filters.printer)
        
        if filters.discipline:
            query = query.filter_by(discipline=filters.discipline)
        
        jobs = query.all()
        
        # Apply search filter (done in-memory for flexibility)
        if filters.search:
            search_term = filters.search.lower()
            jobs = [
                job for job in jobs 
                if search_term in job.student_name.lower() 
                or search_term in job.student_email.lower()
            ]
        
        return jobs
    
    def get_job_counts(self, search: Optional[str] = None) -> Dict[str, int]:
        """
        Get job counts by status with optional search filtering
        
        Args:
            search: Optional search term to filter jobs
            
        Returns:
            Dictionary mapping status to count
        """
        query = Job.query
        
        if search:
            # Apply search filter to the query
            query = query.filter(
                or_(
                    Job.student_name.ilike(f'%{search}%'),
                    Job.student_email.ilike(f'%{search}%')
                )
            )
        
        # Group by status and count
        rows = query.with_entities(Job.status, func.count()).group_by(Job.status).all()
        
        # Convert to dictionary
        counts = {status: int(count) for status, count in rows}
        
        return counts
