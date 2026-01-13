"""add user phone and report model

Revision ID: 0002_add_user_phone_report
Revises: 0001_initial
Create Date: 2026-01-12 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_user_phone_report'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(length=30), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    # alter free_attempts_used to BigInteger (Postgres uses bigint)
    op.alter_column('users', 'free_attempts_used', type_=sa.BigInteger(), existing_type=sa.Integer())

    op.create_table(
        'reports',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('run_id', sa.BigInteger(), nullable=False),
        sa.Column('pdf_path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['run_id'], ['processing_runs.id'], name='reports_run_id_fkey')
    )


def downgrade():
    op.drop_table('reports')
    op.alter_column('users', 'free_attempts_used', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'phone')