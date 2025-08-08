import click
from flask.cli import with_appcontext
from .models.staff import Staff
from .models.job import Job
from .models.event import Event
from datetime import datetime
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
