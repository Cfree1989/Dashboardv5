"""Add locked_by and locked_until to job table

Revision ID: 7d9a1e2f3b4c
Revises: 6886e904fbad
Create Date: 2025-08-19 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7d9a1e2f3b4c'
down_revision = '6886e904fbad'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('job', sa.Column('locked_by', sa.String(length=100), nullable=True))
    op.add_column('job', sa.Column('locked_until', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('job', 'locked_until')
    op.drop_column('job', 'locked_by')
