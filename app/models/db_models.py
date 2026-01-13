from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class SubscriptionPlans(Base):
    __tablename__ = 'subscription_plans'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='subscription_plans_pkey'),
        UniqueConstraint('name', name='subscription_plans_name_key'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    free_attempts_limit: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))

    users: Mapped[list['Users']] = relationship('Users', back_populates='plan')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint('free_attempts_used >= 0', name='users_free_attempts_used_check'),
        CheckConstraint("role::text = ANY (ARRAY['USER'::character varying, 'ADMIN'::character varying]::text[])", name='users_role_check'),
        ForeignKeyConstraint(['plan_id'], ['public.subscription_plans.id'], name='users_plan_id_fkey'),
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'USER'::character varying"))
    plan_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    free_attempts_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    name: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(30))

    plan: Mapped['SubscriptionPlans'] = relationship('SubscriptionPlans', back_populates='users')
    input_images: Mapped[list['InputImages']] = relationship('InputImages', back_populates='user')
    processing_runs: Mapped[list['ProcessingRuns']] = relationship('ProcessingRuns', back_populates='user')


class InputImages(Base):
    __tablename__ = 'input_images'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE', name='input_images_user_id_fkey'),
        PrimaryKeyConstraint('id', name='input_images_pkey'),
        Index('idx_input_images_user_id', 'user_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    meta_json: Mapped[Optional[dict]] = mapped_column(JSONB)

    user: Mapped['Users'] = relationship('Users', back_populates='input_images')
    processing_runs: Mapped[list['ProcessingRuns']] = relationship('ProcessingRuns', back_populates='input_image')


class ProcessingRuns(Base):
    __tablename__ = 'processing_runs'
    __table_args__ = (
        CheckConstraint("index_type::text = ANY (ARRAY['NDVI'::character varying, 'GNDVI'::character varying]::text[])", name='processing_runs_index_type_check'),
        CheckConstraint("status::text = ANY (ARRAY['QUEUED'::character varying, 'RUNNING'::character varying, 'SUCCESS'::character varying, 'FAILED'::character varying, 'BLOCKED'::character varying]::text[])", name='processing_runs_status_check'),
        ForeignKeyConstraint(['input_image_id'], ['public.input_images.id'], ondelete='CASCADE', name='processing_runs_input_image_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE', name='processing_runs_user_id_fkey'),
        PrimaryKeyConstraint('id', name='processing_runs_pkey'),
        Index('idx_processing_runs_status', 'status'),
        Index('idx_processing_runs_user_id', 'user_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_image_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    index_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'QUEUED'::character varying"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))
    metrics_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    input_image: Mapped['InputImages'] = relationship('InputImages', back_populates='processing_runs')
    user: Mapped['Users'] = relationship('Users', back_populates='processing_runs')
    output_artifacts: Mapped[list['OutputArtifacts']] = relationship('OutputArtifacts', back_populates='processing_run')


class OutputArtifacts(Base):
    __tablename__ = 'output_artifacts'
    __table_args__ = (
        CheckConstraint("artifact_type::text = ANY (ARRAY['VISUAL_PNG'::character varying, 'INDEX_TIFF'::character varying, 'REPORT_PDF'::character varying]::text[])", name='output_artifacts_artifact_type_check'),
        ForeignKeyConstraint(['processing_run_id'], ['public.processing_runs.id'], ondelete='CASCADE', name='output_artifacts_processing_run_id_fkey'),
        PrimaryKeyConstraint('id', name='output_artifacts_pkey'),
        Index('idx_output_artifacts_run_id', 'processing_run_id'),
        {'schema': 'public'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    processing_run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, server_default=text('now()'))

    processing_run: Mapped['ProcessingRuns'] = relationship('ProcessingRuns', back_populates='output_artifacts')
