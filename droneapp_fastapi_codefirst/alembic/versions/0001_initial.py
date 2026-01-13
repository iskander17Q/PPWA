"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('free_attempts_limit', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'))
    )

    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=True),
        sa.Column('role', sa.String(length=10), nullable=False, server_default=sa.text("'USER'::character varying")),
        sa.Column('plan_id', sa.BigInteger(), nullable=False),
        sa.Column('free_attempts_used', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], name='users_plan_id_fkey')
    )

    op.create_table(
        'input_images',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='input_images_user_id_fkey')
    )

    op.create_table(
        'processing_runs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('input_image_id', sa.BigInteger(), nullable=False),
        sa.Column('index_type', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False, server_default=sa.text("'QUEUED'::character varying")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['input_image_id'], ['input_images.id'], name='processing_runs_input_image_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='processing_runs_user_id_fkey')
    )

    op.create_table(
        'output_artifacts',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('processing_run_id', sa.BigInteger(), nullable=False),
        sa.Column('artifact_type', sa.String(length=20), nullable=False),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['processing_run_id'], ['processing_runs.id'], name='output_artifacts_processing_run_id_fkey')
    )


def downgrade():
    op.drop_table('output_artifacts')
    op.drop_table('processing_runs')
    op.drop_table('input_images')
    op.drop_table('users')
    op.drop_table('subscription_plans')
