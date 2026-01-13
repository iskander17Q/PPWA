from fastapi import FastAPI, Depends, HTTPException
from typing import List
from app.db import get_db
from sqlalchemy.orm import Session
from app.accessors.users_accessor import UsersAccessor
from app.accessors.runs_accessor import RunsAccessor

app = FastAPI(title="DroneApp - Lab 3 Database First")


def _serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "free_attempts_used": user.free_attempts_used,
        "phone": getattr(user, "phone", None),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_run(run):
    return {
        "id": run.id,
        "index_type": run.index_type,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


@app.get("/users", response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    accessor = UsersAccessor(db)
    users = accessor.list_users()
    return [_serialize_user(u) for u in users]


@app.get("/runs", response_model=List[dict])
def get_runs(db: Session = Depends(get_db)):
    accessor = RunsAccessor(db)
    runs = accessor.list_runs()
    return [_serialize_run(r) for r in runs]






from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, DateTime, func, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    free_attempts_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(), server_default=func.now())
    users: Mapped[list["User"]] = relationship(back_populates="plan")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="USER")
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), nullable=False)
    free_attempts_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    last_login_at: Mapped[str | None] = mapped_column(DateTime())
    created_at: Mapped[str] = mapped_column(DateTime(), server_default=func.now())

    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="users")
    runs: Mapped[list["ProcessingRun"]] = relationship(back_populates="user")  # lazy by default

class ProcessingRun(Base):
    __tablename__ = "processing_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    index_type: Mapped[str] = mapped_column(String(10), nullable=False)  # NDVI/GNDVI
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="QUEUED")
    created_at: Mapped[str] = mapped_column(DateTime(), server_default=func.now())
    user: Mapped["User"] = relationship(back_populates="runs")

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("processing_runs.id"), nullable=False)
    pdf_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(), server_default=func.now())


    # Shell command to create DB removed from source file to avoid SyntaxError during imports
    # (If needed, run DB creation from shell or migration scripts.)