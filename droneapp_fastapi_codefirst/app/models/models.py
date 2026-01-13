from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    free_attempts_limit = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    users = relationship('User', back_populates='plan')


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(120))
    role = Column(String(10), nullable=False, server_default="USER")
    plan_id = Column(BigInteger, ForeignKey('subscription_plans.id'), nullable=False)
    free_attempts_used = Column(Integer, nullable=False, server_default='0')
    is_active = Column(Boolean, nullable=False, server_default='true')
    phone = Column(String(30))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    plan = relationship('SubscriptionPlan', back_populates='users')
    input_images = relationship('InputImage', back_populates='user')
    processing_runs = relationship('ProcessingRun', back_populates='user')


class InputImage(Base):
    __tablename__ = 'input_images'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='input_images')
    processing_runs = relationship('ProcessingRun', back_populates='input_image')


class ProcessingRun(Base):
    __tablename__ = 'processing_runs'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'), nullable=False)
    input_image_id = Column(BigInteger, ForeignKey('input_images.id'), nullable=False)
    index_type = Column(String(10), nullable=False)
    status = Column(String(10), nullable=False, server_default='QUEUED')
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship('User', back_populates='processing_runs')
    input_image = relationship('InputImage', back_populates='processing_runs')
    output_artifacts = relationship('OutputArtifact', back_populates='processing_run')


class OutputArtifact(Base):
    __tablename__ = 'output_artifacts'

    id = Column(BigInteger, primary_key=True)
    processing_run_id = Column(BigInteger, ForeignKey('processing_runs.id'), nullable=False)
    artifact_type = Column(String(20), nullable=False)
    storage_path = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    processing_run = relationship('ProcessingRun', back_populates='output_artifacts')
