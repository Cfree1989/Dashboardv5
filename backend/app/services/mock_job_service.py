"""
Mock Job Service for generating test data with correct pricing calculations.
"""

import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from app import db
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment


class MockJobService:
    """Service for generating realistic mock jobs for testing."""
    
    # Pricing constants
    FILAMENT_RATE = 0.10  # $0.10/g
    RESIN_RATE = 0.20     # $0.20/g
    MINIMUM_CHARGE = 3.00  # $3.00 minimum
    
    # Material and diversity options
    MATERIALS = ['Filament', 'Resin']
    FILAMENT_COLORS = ['Gray', 'Black', 'Blue', 'Red', 'Green', 'White', 'True Red', 'True Orange', 'True Yellow', 'Lime Green', 'Forest Green', 'Electric Blue', 'True Black', 'Brown']
    RESIN_COLORS = ['Clear', 'White', 'Black', 'Gray', 'Blue', 'Red']
    PRINTERS = ['Prusa MK4S', 'Raise3D Pro2', 'Formlabs Form 3']
    
    DISCIPLINES = {
        'Engineering': ['MECH 1010', 'CIV 2010', 'EE 3010', 'CS 4010', 'MECH 3010', 'CIV 3010'],
        'Art': ['ART 1010', 'SCULP 2010', 'DESIGN 3010', 'PHOTO 4010', 'ART 2010', 'SCULP 3010'],
        'Architecture': ['ARCH 1010', 'ARCH 2010', 'ARCH 3010', 'ARCH 4010'],
        'Science': ['BIO 1010', 'CHEM 2010', 'PHYS 3010', 'ENV 4010', 'BIO 2010', 'CHEM 3010']
    }
    
    # Realistic notes pool
    NOTES_POOL = [
        "Please print with 20% infill for strength",
        "Student requested rush order for final project",
        "File had some issues, fixed in slicer",
        "Customer picked up early, very satisfied",
        "Minor quality issues, customer was understanding",
        "Perfect print quality, no issues",
        "Adjusted print settings for better surface finish",
        "Student requested specific color, matched perfectly",
        "Large print, took longer than estimated",
        "Small print, completed quickly",
        "Customer was very happy with the result",
        "Minor support removal required",
        "Print came out exactly as expected",
        "Student requested reprint due to design changes",
        "Excellent adhesion, no warping issues"
    ]
    
    # Weight buckets for realistic distribution
    WEIGHT_BUCKETS = {
        'Filament': {
            'light': (5, 15),      # 5-15g (minimum charge scenarios)
            'medium': (20, 50),    # 20-50g (typical jobs)
            'heavy': (60, 120)     # 60-120g (large projects)
        },
        'Resin': {
            'light': (3, 10),      # 3-10g (minimum charge scenarios)
            'medium': (12, 25),    # 12-25g (typical jobs)
            'heavy': (30, 60)      # 30-60g (large projects)
        }
    }
    
    @staticmethod
    def calculate_price(grams: float, material: str) -> int:
        """
        Calculate price in cents with correct pricing logic.
        
        Args:
            grams: Weight in grams
            material: 'Filament' or 'Resin'
            
        Returns:
            Price in cents
        """
        rate = MockJobService.FILAMENT_RATE if material.lower() == 'filament' else MockJobService.RESIN_RATE
        raw_cost = grams * rate
        final_cost = max(raw_cost, MockJobService.MINIMUM_CHARGE)
        return int(Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
    
    @staticmethod
    def generate_realistic_weight(material: str) -> float:
        """Generate a realistic weight for the given material."""
        buckets = MockJobService.WEIGHT_BUCKETS[material]
        # Weight distribution: 40% light, 45% medium, 15% heavy
        rand = random.random()
        if rand < 0.4:
            bucket = 'light'
        elif rand < 0.85:
            bucket = 'medium'
        else:
            bucket = 'heavy'
        
        min_weight, max_weight = buckets[bucket]
        return round(random.uniform(min_weight, max_weight), 1)
    
    @staticmethod
    def generate_job_data(
        status: str,
        student_email: str = "cfree3@lsu.edu",
        add_notes: bool = True,
        seed: Optional[int] = None
    ) -> Dict:
        """Generate realistic job data for a given status."""
        if seed is not None:
            random.seed(seed)
        
        # Generate basic job info
        material = random.choice(MockJobService.MATERIALS)
        color = random.choice(MockJobService.FILAMENT_COLORS if material == 'Filament' else MockJobService.RESIN_COLORS)
        printer = random.choice(MockJobService.PRINTERS)
        discipline = random.choice(list(MockJobService.DISCIPLINES.keys()))
        class_number = random.choice(MockJobService.DISCIPLINES[discipline])
        
        # Generate student name
        first_names = ['Alex', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'James', 'Maria', 'Robert', 'Jennifer', 'Christopher', 'Amanda', 'Thomas', 'Rachel', 'Daniel', 'Jessica', 'Brandon', 'Megan', 'Kevin', 'Ashley']
        last_names = ['Chen', 'Johnson', 'Rodriguez', 'Wilson', 'Kim', 'Thompson', 'Brown', 'Garcia', 'Lee', 'Davis', 'Miller', 'Taylor', 'Anderson', 'Green', 'White', 'Park', 'Williams', 'Davis', 'Wilson', 'Thompson']
        
        student_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Generate weight and calculate pricing
        weight = MockJobService.generate_realistic_weight(material)
        estimated_cost = MockJobService.calculate_price(weight, material) / 100.0
        
        # Generate timestamps based on status
        now = datetime.utcnow()
        days_ago = random.randint(0, 14)  # Jobs from last 2 weeks
        
        if status == 'UPLOADED':
            created_at = now - timedelta(days=days_ago)
            updated_at = created_at
        elif status == 'PENDING':
            created_at = now - timedelta(days=days_ago + 1)
            updated_at = now - timedelta(days=days_ago)
        elif status == 'READYTOPRINT':
            created_at = now - timedelta(days=days_ago + 2)
            updated_at = now - timedelta(days=days_ago)
        elif status == 'PRINTING':
            created_at = now - timedelta(days=days_ago + 3)
            updated_at = now - timedelta(days=days_ago)
        elif status == 'COMPLETED':
            created_at = now - timedelta(days=days_ago + 4)
            updated_at = now - timedelta(days=days_ago)
        elif status == 'PAIDPICKEDUP':
            created_at = now - timedelta(days=days_ago + 5)
            updated_at = now - timedelta(days=days_ago)
        else:
            created_at = now - timedelta(days=days_ago)
            updated_at = created_at
        
        # Generate notes if requested
        notes = None
        if add_notes and random.random() < 0.7:  # 70% chance of notes
            notes = random.choice(MockJobService.NOTES_POOL)
        
        # Generate file info
        jid = uuid.uuid4().hex
        short_id = jid[:8]
        filename = f"{student_name.replace(' ', '_')}_model_{short_id}.stl"
        
        return {
            'id': jid,
            'short_id': short_id,
            'student_name': student_name,
            'student_email': student_email,
            'discipline': discipline,
            'class_number': class_number,
            'original_filename': filename,
            'display_name': filename,
            'file_path': f"storage/{status}/{filename}",
            'metadata_path': f"storage/{status}/{filename.replace('.stl', '_metadata.json')}",
            'printer': printer,
            'color': color,
            'material': material,
            'weight_g': weight,
            'time_hours': round(weight / 10, 1),  # Rough estimate: 1 hour per 10g
            'cost_usd': estimated_cost,
            'status': status,
            'created_at': created_at,
            'updated_at': updated_at,
            'notes': notes,
            'student_confirmed': status in ['READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP'],
            'student_confirmed_at': created_at + timedelta(hours=2) if status in ['READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP'] else None
        }
    
    @staticmethod
    def create_job_with_events(job_data: Dict, staff_name: str = "Admin") -> Job:
        """Create a job with appropriate events based on status."""
        job = Job(**job_data)
        db.session.add(job)
        db.session.flush()
        
        # Add events based on job status
        events = []
        
        # JobCreated event
        events.append(Event(
            job_id=job.id,
            event_type='JobCreated',
            details={},
            triggered_by='system',
            workstation_id='mock-generator',
            timestamp=job.created_at
        ))
        
        # StaffApproved event (for all non-UPLOADED jobs)
        if job.status != 'UPLOADED':
            events.append(Event(
                job_id=job.id,
                event_type='StaffApproved',
                details={},
                triggered_by=staff_name,
                workstation_id='mock-generator',
                timestamp=job.created_at + timedelta(hours=1)
            ))
        
        # StudentConfirmed event (for confirmed jobs)
        if job.student_confirmed:
            events.append(Event(
                job_id=job.id,
                event_type='StudentConfirmed',
                details={},
                triggered_by='student',
                workstation_id='mock-generator',
                timestamp=job.student_confirmed_at
            ))
        
        # JobMarkedPrinting event
        if job.status in ['PRINTING', 'COMPLETED', 'PAIDPICKEDUP']:
            events.append(Event(
                job_id=job.id,
                event_type='JobMarkedPrinting',
                details={},
                triggered_by=staff_name,
                workstation_id='mock-generator',
                timestamp=job.created_at + timedelta(days=1)
            ))
        
        # JobMarkedComplete event
        if job.status in ['COMPLETED', 'PAIDPICKEDUP']:
            events.append(Event(
                job_id=job.id,
                event_type='JobMarkedComplete',
                details={},
                triggered_by=staff_name,
                workstation_id='mock-generator',
                timestamp=job.updated_at - timedelta(days=1)
            ))
        
        # Add all events
        for event in events:
            db.session.add(event)
        
        return job
    
    @staticmethod
    def create_payment_for_job(job: Job, staff_name: str = "Admin") -> Payment:
        """Create a payment for a PAIDPICKEDUP job."""
        # For paid jobs, use actual weight (might be different from estimated)
        actual_weight = job.weight_g * random.uniform(0.8, 1.2)  # ±20% variation
        actual_weight = round(actual_weight, 1)
        
        actual_price_cents = MockJobService.calculate_price(actual_weight, job.material)
        
        payment = Payment(
            job_id=job.id,
            grams=actual_weight,
            price_cents=actual_price_cents,
            txn_no=f"TXN{job.short_id.upper()}",
            picked_up_by=job.student_name,
            paid_ts=job.updated_at,
            paid_by_staff=staff_name
        )
        
        db.session.add(payment)
        
        # Add payment event
        db.session.add(Event(
            job_id=job.id,
            event_type='JobMarkedPickedUp',
            details={'payment_amount': actual_price_cents / 100.0},
            triggered_by=staff_name,
            workstation_id='mock-generator',
            timestamp=job.updated_at
        ))
        
        return payment
    
    @staticmethod
    def generate_mock_jobs(
        counts: Dict[str, int],
        student_email: str = "cfree3@lsu.edu",
        add_notes: bool = True,
        seed: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Generate mock jobs according to the specified counts.
        
        Args:
            counts: Dict with status as key and count as value
            student_email: Email to use for all jobs
            add_notes: Whether to add notes to jobs
            seed: Random seed for reproducible generation
            
        Returns:
            Dict with actual counts created for each status
        """
        from flask import current_app
        
        # Safety check: only allow in development
        if not current_app.config.get('DEBUG', False):
            raise RuntimeError("Mock job generation is only allowed in development mode")
        
        if seed is not None:
            random.seed(seed)
        
        created_counts = {}
        
        for status, count in counts.items():
            if count <= 0:
                created_counts[status] = 0
                continue
                
            jobs_created = 0
            for i in range(count):
                # Generate unique seed for each job to ensure diversity
                job_seed = seed + i * 1000 if seed is not None else None
                if job_seed is not None:
                    random.seed(job_seed)
                
                job_data = MockJobService.generate_job_data(
                    status=status,
                    student_email=student_email,
                    add_notes=add_notes,
                    seed=job_seed
                )
                
                job = MockJobService.create_job_with_events(job_data)
                
                # Create payment for PAIDPICKEDUP jobs
                if status == 'PAIDPICKEDUP':
                    MockJobService.create_payment_for_job(job)
                
                jobs_created += 1
            
            created_counts[status] = jobs_created
        
        db.session.commit()
        return created_counts

    @staticmethod
    def generate_randomized_jobs(
        status_counts: Dict[str, int],
        student_email: str = "cfree3@lsu.edu",
        seed: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Simplified randomizer: just specify which tab (status) and how many jobs.
        Everything else is randomized while following pricing rules.
        
        Args:
            status_counts: Dict with status as key and count as value (e.g., {'UPLOADED': 5, 'COMPLETED': 3})
            student_email: Email to use for all jobs (default: cfree3@lsu.edu)
            seed: Random seed for reproducible generation
            
        Returns:
            Dict with actual counts created for each status
        """
        from flask import current_app
        
        # Safety check: only allow in development
        if not current_app.config.get('DEBUG', False):
            raise RuntimeError("Mock job generation is only allowed in development mode")
        
        if seed is not None:
            random.seed(seed)
        
        created_counts = {}
        
        for status, count in status_counts.items():
            if count <= 0:
                created_counts[status] = 0
                continue
                
            jobs_created = 0
            for i in range(count):
                # Generate unique seed for each job to ensure diversity
                job_seed = seed + i * 1000 if seed is not None else None
                if job_seed is not None:
                    random.seed(job_seed)
                
                # Generate job with full randomization
                job_data = MockJobService.generate_job_data(
                    status=status,
                    student_email=student_email,
                    add_notes=True,  # Always add notes for variety
                    seed=job_seed
                )
                
                job = MockJobService.create_job_with_events(job_data)
                
                # Create payment for PAIDPICKEDUP jobs
                if status == 'PAIDPICKEDUP':
                    MockJobService.create_payment_for_job(job)
                
                jobs_created += 1
            
            created_counts[status] = jobs_created
        
        db.session.commit()
        return created_counts

    @staticmethod
    def delete_jobs_by_email(student_email: str = "cfree3@lsu.edu") -> Dict[str, int]:
        """
        Delete all jobs with a specific email address (development only).
        
        Args:
            student_email: Email address to match for deletion (default: cfree3@lsu.edu)
            
        Returns:
            Dict with counts of deleted items
        """
        from flask import current_app
        
        # Safety check: only allow in development
        if not current_app.config.get('DEBUG', False):
            raise RuntimeError("Job deletion is only allowed in development mode")
        
        # Count jobs before deletion
        jobs_to_delete = Job.query.filter_by(student_email=student_email).all()
        job_count = len(jobs_to_delete)
        
        if job_count == 0:
            return {'jobs_deleted': 0, 'events_deleted': 0, 'payments_deleted': 0}
        
        # Get job IDs for related deletions
        job_ids = [job.id for job in jobs_to_delete]
        
        # Delete related payments
        payments_deleted = Payment.query.filter(Payment.job_id.in_(job_ids)).delete()
        
        # Delete related events
        events_deleted = Event.query.filter(Event.job_id.in_(job_ids)).delete()
        
        # Delete jobs
        jobs_deleted = Job.query.filter_by(student_email=student_email).delete()
        
        db.session.commit()
        
        return {
            'jobs_deleted': jobs_deleted,
            'events_deleted': events_deleted,
            'payments_deleted': payments_deleted
        }

    @staticmethod
    def delete_all_jobs() -> Dict[str, int]:
        """
        Delete ALL jobs from the entire system (development only).
        
        Returns:
            Dict with counts of deleted items
        """
        from flask import current_app
        
        # Safety check: only allow in development
        if not current_app.config.get('DEBUG', False):
            raise RuntimeError("Mass job deletion is only allowed in development mode")
        
        # Count all jobs before deletion
        total_jobs = Job.query.count()
        
        if total_jobs == 0:
            return {'jobs_deleted': 0, 'events_deleted': 0, 'payments_deleted': 0}
        
        # Delete all payments first (foreign key constraint)
        payments_deleted = Payment.query.delete()
        
        # Delete all events
        events_deleted = Event.query.delete()
        
        # Delete all jobs
        jobs_deleted = Job.query.delete()
        
        db.session.commit()
        
        return {
            'jobs_deleted': jobs_deleted,
            'events_deleted': events_deleted,
            'payments_deleted': payments_deleted
        }
