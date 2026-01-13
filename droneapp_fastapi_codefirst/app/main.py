from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from typing import List
from app.db import get_db
from sqlalchemy.orm import Session
from app.accessors.users_accessor import UsersAccessor
from app.accessors.runs_accessor import RunsAccessor
from app.controllers import users_controller

app = FastAPI(title='DroneApp CodeFirst Lab 5 - MVC')
app.include_router(users_controller.router)


def _serialize_user_basic(user):
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_run_basic(run):
    return {
        'id': run.id,
        'index_type': run.index_type,
        'status': run.status,
        'created_at': run.created_at.isoformat() if run.created_at else None,
    }


@app.get('/api/users', response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    accessor = UsersAccessor(db)
    users = accessor.list_users()
    return [_serialize_user_basic(u) for u in users]


@app.get('/api/runs', response_model=List[dict])
def get_runs(db: Session = Depends(get_db)):
    accessor = RunsAccessor(db)
    runs = accessor.list_runs()
    return [_serialize_run_basic(r) for r in runs]


@app.get('/api/users-eager', response_model=List[dict])
def get_users_eager(db: Session = Depends(get_db)):
    accessor = UsersAccessor(db)
    users = accessor.list_users_with_runs_eager()
    return [{'id': u.id, 'email': u.email, 'runs_count': len(u.processing_runs)} for u in users]


@app.get('/api/users-lazy', response_model=List[dict])
def get_users_lazy(db: Session = Depends(get_db)):
    accessor = UsersAccessor(db)
    users = accessor.list_users()
    # Access processing_runs attribute which will lazy load per user (demonstrates N+1)
    return [{'id': u.id, 'email': u.email, 'runs_count': len(u.processing_runs)} for u in users]


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/users")
