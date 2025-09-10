"""Merge heads: unreviewed/attention flags and event fk changes

Revision ID: b1c2d3e4f5a6
Revises: 211b02203aa4, 8f2b3c9d12ab
Create Date: 2025-09-10 17:16:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = ('211b02203aa4', '8f2b3c9d12ab')
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration - no schema changes required.
    pass


def downgrade():
    # Downgrade would require splitting branches; leave as no-op.
    pass


