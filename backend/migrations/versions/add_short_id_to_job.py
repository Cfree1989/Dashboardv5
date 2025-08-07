"""add short_id to job

Revision ID: 3a1f9d2b7e10
Revises: c55b0ceeb21b
Create Date: 2025-08-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a1f9d2b7e10'
down_revision = 'c55b0ceeb21b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('job', sa.Column('short_id', sa.String(length=12), nullable=True))
    op.create_index('ix_job_short_id', 'job', ['short_id'], unique=True)


def downgrade():
    op.drop_index('ix_job_short_id', table_name='job')
    op.drop_column('job', 'short_id')


