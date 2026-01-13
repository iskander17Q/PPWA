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
