import click
from flask.cli import with_appcontext
from .models.staff import Staff
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

def init_app(app):
    app.cli.add_command(seed_data_command)
