"""Add is_unreviewed and needs_attention to job

Revision ID: 8f2b3c9d12ab
Revises: 7d9a1e2f3b4c
Create Date: 2025-09-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8f2b3c9d12ab'
down_revision = '7d9a1e2f3b4c'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns with safe server defaults
    op.add_column('job', sa.Column('is_unreviewed', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.add_column('job', sa.Column('needs_attention', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    # Backfill based on current status
    op.execute("""
        UPDATE job
        SET is_unreviewed = CASE WHEN status = 'UPLOADED' THEN TRUE ELSE FALSE END
    """)
    op.execute("""
        UPDATE job
        SET needs_attention = FALSE
    """)


def downgrade():
    op.drop_column('job', 'needs_attention')
    op.drop_column('job', 'is_unreviewed')


