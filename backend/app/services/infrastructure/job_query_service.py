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
                 printer: Optional[str] = None, discipline: Optional[str] = None,
                 needs_attention: Optional[bool] = None):
        self.status = status
        self.search = search
        self.printer = printer
        self.discipline = discipline
        self.needs_attention = needs_attention


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
        import logging
        from app import db
        logger = logging.getLogger(__name__)
        
        # Force database session refresh to see latest committed changes
        db.session.expire_all()
        
        logger.info(f"[JOB-QUERY-TIMING] Starting query for status={filters.status}")
        query = Job.query
        
        # Apply database-level filters
        if filters.status:
            query = query.filter_by(status=filters.status)
        
        if filters.printer:
            query = query.filter_by(printer=filters.printer)
        
        if filters.discipline:
            query = query.filter_by(discipline=filters.discipline)
        if filters.needs_attention is True:
            query = query.filter_by(needs_attention=True)
        
        import time
        query_start = time.time()
        jobs = query.all()
        query_time = (time.time() - query_start) * 1000
        
        logger.info(f"[JOB-QUERY-TIMING] Query completed in {query_time:.2f}ms, found {len(jobs)} jobs with status={filters.status}")
        
        # Apply search filter (done in-memory for flexibility)
        if filters.search:
            search_term = filters.search.lower()
            jobs = [
                job for job in jobs 
                if search_term in job.student_name.lower() 
                or search_term in job.student_email.lower()
            ]
            logger.info(f"[JOB-QUERY-TIMING] After search filter, {len(jobs)} jobs remain")
        
        return jobs
    
    def get_job_counts(self, search: Optional[str] = None) -> Dict[str, int]:
        """
        Get job counts by status with optional search filtering
        
        Args:
            search: Optional search term to filter jobs
            
        Returns:
            Dictionary mapping status to count
        """
        import logging
        from app import db
        logger = logging.getLogger(__name__)
        
        # Force database session refresh to see latest committed changes
        db.session.expire_all()
        
        logger.info(f"[JOB-COUNT-TIMING] Starting job counts query with search={search}")
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
        import time
        query_start = time.time()
        rows = query.with_entities(Job.status, func.count()).group_by(Job.status).all()
        query_time = (time.time() - query_start) * 1000
        
        # Convert to dictionary
        counts = {status: int(count) for status, count in rows}
        
        logger.info(f"[JOB-COUNT-TIMING] Query completed in {query_time:.2f}ms, counts: {counts}")
        
        return counts
