import click
from flask.cli import with_appcontext
from .models.staff import Staff
from .models.job import Job
from .models.event import Event
from .services.mock_job_service import MockJobService
from datetime import datetime
import random
import uuid
from . import db

@click.command('seed-data')
@with_appcontext
def seed_data_command():
    """Seeds the database with initial data."""
    if Staff.query.first():
        click.echo('Staff table already seeded.')
        return

    staff_members = [
        Staff(name='John Doe', is_active=True),
        Staff(name='Jane Smith', is_active=True),
        Staff(name='Admin User', is_active=True),
        Staff(name='Peter Jones', is_active=False)
    ]

    db.session.bulk_save_objects(staff_members)
    db.session.commit()
    click.echo('Seeded staff table.')

@click.command('seed-demo-jobs')
@with_appcontext
def seed_demo_jobs_command():
    """Seeds demo jobs across statuses to enable UI testing of transitions."""
    demo_exists = Job.query.first() is not None
    if demo_exists:
        click.echo('Jobs already exist; adding additional demo jobs.')

    def make_job(status: str, idx: int, material: str = 'Filament'):
        jid = uuid.uuid4().hex
        short = jid[:8]
        job = Job(
            id=jid,
            short_id=short,
            student_name=f'Demo Student {idx}',
            student_email=f'demo{idx}@example.com',
            discipline='Engineering',
            class_number='ENGR 1010',
            original_filename=f'DemoModel_{short}.stl',
            display_name=f'DemoModel_{short}.stl',
            file_path=f'storage/{status.title() if status != "READYTOPRINT" else "ReadyToPrint"}/DemoModel_{short}.stl',
            metadata_path=f'storage/{status.title() if status != "READYTOPRINT" else "ReadyToPrint"}/DemoModel_{short}_metadata.json',
            printer='Prusa MK4S',
            color='Gray',
            material=material,
            status=status,
            weight_g=25.0 if status in ('PENDING','READYTOPRINT','PRINTING','COMPLETED','PAIDPICKEDUP') else None,
            time_hours=1.5 if status in ('PENDING','READYTOPRINT','PRINTING','COMPLETED','PAIDPICKEDUP') else None,
            cost_usd=5.0 if status in ('PENDING','READYTOPRINT','PRINTING','COMPLETED','PAIDPICKEDUP') else None,
        )
        db.session.add(job)
        db.session.flush()
        db.session.add(Event(job_id=job.id, event_type='JobCreated', details={}, triggered_by='seed', workstation_id='seed'))
        if status in ('PENDING','READYTOPRINT','PRINTING','COMPLETED','PAIDPICKEDUP'):
            db.session.add(Event(job_id=job.id, event_type='StaffApproved', details={}, triggered_by='seed', workstation_id='seed'))
        if status in ('READYTOPRINT','PRINTING','COMPLETED','PAIDPICKEDUP'):
            db.session.add(Event(job_id=job.id, event_type='StudentConfirmed', details={}, triggered_by='seed', workstation_id='seed'))
        if status in ('PRINTING','COMPLETED','PAIDPICKEDUP'):
            db.session.add(Event(job_id=job.id, event_type='JobMarkedPrinting', details={}, triggered_by='seed', workstation_id='seed'))
        if status in ('COMPLETED','PAIDPICKEDUP'):
            db.session.add(Event(job_id=job.id, event_type='JobMarkedComplete', details={}, triggered_by='seed', workstation_id='seed'))
        if status == 'PAIDPICKEDUP':
            db.session.add(Event(job_id=job.id, event_type='JobMarkedPickedUp', details={}, triggered_by='seed', workstation_id='seed'))

    # Create two jobs for each key status (READYTOPRINT, PRINTING, COMPLETED)
    statuses = ['READYTOPRINT', 'PRINTING', 'COMPLETED']
    idx = 1
    for st in statuses:
        for _ in range(2):
            make_job(st, idx)
            idx += 1

    db.session.commit()
    click.echo('Seeded demo jobs in READYTOPRINT, PRINTING, and COMPLETED.')

def init_app(app):
    app.cli.add_command(seed_data_command)
    app.cli.add_command(seed_demo_jobs_command)
    app.cli.add_command(seed_uploaded_jobs_command)
    app.cli.add_command(generate_mock_jobs_command)
    app.cli.add_command(randomize_jobs_command)
    app.cli.add_command(delete_jobs_command)
    app.cli.add_command(delete_all_jobs_command)


@click.command('seed-uploaded')
@click.option('--count', default=10, show_default=True, help='Number of UPLOADED jobs to create')
@with_appcontext
def seed_uploaded_jobs_command(count: int):
    """Seeds a number of mock jobs in the UPLOADED status for UI testing."""
    colors = [
        'True Red','True Orange','Light Orange','True Yellow','Dark Yellow','Lime Green','Green','Forest Green',
        'Blue','Electric Blue','Midnight Purple','Light Purple','Clear','True White','Gray','True Black','Brown',
        'Copper','Bronze','True Silver','True Gold'
    ]
    printers = ['Prusa MK4S', 'Prusa XL', 'Raise3D Pro 2 Plus']
    disciplines = ['Art','Architecture','Landscape Architecture','Interior Design','Engineering','Hobby/Personal']

    created = 0
    for idx in range(count):
        jid = uuid.uuid4().hex
        short = jid[:8]
        job = Job(
            id=jid,
            short_id=short,
            student_name=f'Mock Student {idx+1}',
            student_email=f'mock{idx+1}@example.com',
            discipline=random.choice(disciplines),
            class_number='N/A',
            original_filename=f'Mock_{short}.stl',
            display_name=f'Mock_{short}.stl',
            file_path=f'storage/Uploaded/Mock_{short}.stl',
            metadata_path=f'storage/Uploaded/Mock_{short}_metadata.json',
            printer=random.choice(printers),
            color=random.choice(colors),
            material='Filament',
            status='UPLOADED',
        )
        db.session.add(job)
        db.session.flush()
        db.session.add(Event(job_id=job.id, event_type='JobCreated', details={}, triggered_by='seed', workstation_id='seed'))
        created += 1

    db.session.commit()
    click.echo(f'Seeded {created} UPLOADED jobs.')

@click.command('generate-mock-jobs')
@click.option('--uploaded', default=0, help='Number of UPLOADED jobs to create')
@click.option('--pending', default=0, help='Number of PENDING jobs to create')
@click.option('--ready', default=0, help='Number of READYTOPRINT jobs to create')
@click.option('--printing', default=0, help='Number of PRINTING jobs to create')
@click.option('--completed', default=0, help='Number of COMPLETED jobs to create')
@click.option('--paid', default=0, help='Number of PAIDPICKEDUP jobs to create')
@click.option('--email', default='cfree3@lsu.edu', help='Email address for all jobs')
@click.option('--seed', type=int, help='Random seed for reproducible generation')
@click.option('--add-notes/--no-notes', default=True, help='Whether to add notes to jobs')
@with_appcontext
def generate_mock_jobs_command(uploaded, pending, ready, printing, completed, paid, email, seed, add_notes):
    """Generate mock jobs with correct pricing and realistic data."""
    from flask import current_app
    
    # Safety check: only allow in development
    if not current_app.config.get('DEBUG', False):
        click.echo('❌ Mock job generation is only allowed in development mode')
        return 1
    
    counts = {
        'UPLOADED': uploaded,
        'PENDING': pending,
        'READYTOPRINT': ready,
        'PRINTING': printing,
        'COMPLETED': completed,
        'PAIDPICKEDUP': paid
    }
    
    total_requested = sum(counts.values())
    if total_requested == 0:
        click.echo('No jobs requested. Use --help to see options.')
        return
    
    click.echo(f'Generating {total_requested} mock jobs with email: {email}')
    if seed is not None:
        click.echo(f'Using seed: {seed}')
    
    try:
        created_counts = MockJobService.generate_mock_jobs(
            counts=counts,
            student_email=email,
            add_notes=add_notes,
            seed=seed
        )
        
        click.echo('✅ Mock jobs generated successfully!')
        click.echo('Created:')
        for status, count in created_counts.items():
            if count > 0:
                click.echo(f'  {status}: {count} jobs')
        
        total_created = sum(created_counts.values())
        click.echo(f'\nTotal: {total_created} jobs created')
        
    except Exception as e:
        click.echo(f'❌ Error generating mock jobs: {e}')
        return 1

@click.command('randomize-jobs')
@click.option('--uploaded', default=0, help='Number of UPLOADED jobs to create')
@click.option('--pending', default=0, help='Number of PENDING jobs to create')
@click.option('--ready', default=0, help='Number of READYTOPRINT jobs to create')
@click.option('--printing', default=0, help='Number of PRINTING jobs to create')
@click.option('--completed', default=0, help='Number of COMPLETED jobs to create')
@click.option('--paid', default=0, help='Number of PAIDPICKEDUP jobs to create')
@click.option('--email', default='cfree3@lsu.edu', help='Email address for all jobs')
@click.option('--seed', type=int, help='Random seed for reproducible generation')
@with_appcontext
def randomize_jobs_command(uploaded, pending, ready, printing, completed, paid, email, seed):
    """Simplified randomizer: just specify which tab and how many jobs. Everything else is randomized."""
    from flask import current_app
    
    # Safety check: only allow in development
    if not current_app.config.get('DEBUG', False):
        click.echo('❌ Mock job generation is only allowed in development mode')
        return 1
    
    counts = {
        'UPLOADED': uploaded,
        'PENDING': pending,
        'READYTOPRINT': ready,
        'PRINTING': printing,
        'COMPLETED': completed,
        'PAIDPICKEDUP': paid
    }
    
    total_requested = sum(counts.values())
    if total_requested == 0:
        click.echo('No jobs requested. Use --help to see options.')
        return
    
    click.echo(f'🎲 Randomizing {total_requested} jobs across tabs with email: {email}')
    if seed is not None:
        click.echo(f'Using seed: {seed}')
    
    try:
        created_counts = MockJobService.generate_randomized_jobs(
            status_counts=counts,
            student_email=email,
            seed=seed
        )
        
        click.echo('✅ Randomized jobs generated successfully!')
        click.echo('Created:')
        for status, count in created_counts.items():
            if count > 0:
                click.echo(f'  {status}: {count} jobs')
        
        total_created = sum(created_counts.values())
        click.echo(f'\nTotal: {total_created} jobs created')
        click.echo('✨ All details randomized while following pricing rules!')
        
    except Exception as e:
        click.echo(f'❌ Error generating randomized jobs: {e}')
        return 1

@click.command('delete-jobs')
@click.option('--email', default='cfree3@lsu.edu', help='Email address to match for deletion')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def delete_jobs_command(email, confirm):
    """Delete all jobs with a specific email address (development only)."""
    from flask import current_app
    
    # Safety check: only allow in development
    if not current_app.config.get('DEBUG', False):
        click.echo('❌ Job deletion is only allowed in development mode')
        return 1
    
    # Count jobs before deletion
    jobs_to_delete = Job.query.filter_by(student_email=email).all()
    job_count = len(jobs_to_delete)
    
    if job_count == 0:
        click.echo(f'No jobs found with email: {email}')
        return
    
    if not confirm:
        click.echo(f'⚠️  This will delete {job_count} jobs with email: {email}')
        click.echo('This action cannot be undone!')
        if not click.confirm('Are you sure you want to continue?'):
            click.echo('Deletion cancelled.')
            return
    
    try:
        deleted_counts = MockJobService.delete_jobs_by_email(email)
        
        click.echo('🗑️  Jobs deleted successfully!')
        click.echo(f'Deleted:')
        click.echo(f'  Jobs: {deleted_counts["jobs_deleted"]}')
        click.echo(f'  Events: {deleted_counts["events_deleted"]}')
        click.echo(f'  Payments: {deleted_counts["payments_deleted"]}')
        
    except Exception as e:
        click.echo(f'❌ Error deleting jobs: {e}')
        return 1

@click.command('delete-all-jobs')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def delete_all_jobs_command(confirm):
    """Delete ALL jobs from the entire system (development only)."""
    from flask import current_app
    
    # Safety check: only allow in development
    if not current_app.config.get('DEBUG', False):
        click.echo('❌ Mass job deletion is only allowed in development mode')
        return 1
    
    # Count all jobs before deletion
    total_jobs = Job.query.count()
    total_events = Event.query.count()
    total_payments = Payment.query.count()
    
    if total_jobs == 0:
        click.echo('No jobs found in the system.')
        return
    
    if not confirm:
        click.echo(f'⚠️  ⚠️  ⚠️  DANGER ZONE ⚠️  ⚠️  ⚠️')
        click.echo(f'This will delete ALL jobs from the entire system:')
        click.echo(f'  Jobs: {total_jobs}')
        click.echo(f'  Events: {total_events}')
        click.echo(f'  Payments: {total_payments}')
        click.echo('This action cannot be undone!')
        click.echo('Type "DELETE ALL" to confirm:')
        
        confirmation = input().strip()
        if confirmation != "DELETE ALL":
            click.echo('Deletion cancelled.')
            return
    
    try:
        deleted_counts = MockJobService.delete_all_jobs()
        
        click.echo('🗑️  All jobs deleted successfully!')
        click.echo(f'Deleted:')
        click.echo(f'  Jobs: {deleted_counts["jobs_deleted"]}')
        click.echo(f'  Events: {deleted_counts["events_deleted"]}')
        click.echo(f'  Payments: {deleted_counts["payments_deleted"]}')
        click.echo('✨ System is now clean and ready for fresh testing!')
        
    except Exception as e:
        click.echo(f'❌ Error deleting all jobs: {e}')
        return 1
