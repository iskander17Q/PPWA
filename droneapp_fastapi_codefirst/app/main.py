from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from typing import List
from app.db import get_db
from sqlalchemy.orm import Session
from app.accessors.users_accessor import UsersAccessor
from app.accessors.runs_accessor import RunsAccessor
from .controllers import users_controller, runs_controller

app = FastAPI(title='DroneApp CodeFirst Lab 6 - MVC complex')
app.include_router(users_controller.router)
app.include_router(runs_controller.router)


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


from app.api.routes import runs_api
app.include_router(runs_api.router)

# Lab8 analyze API + UI
from app.api import analyze_api
from app.controllers import analyze_ui_controller, users_controller, runs_controller
from app.controllers import analyze_ui_controller
from app.controllers import users_controller

app.include_router(analyze_api.router)
app.include_router(analyze_ui_controller.router)

# Auth controllers
from app.controllers import auth_controller
app.include_router(auth_controller.router)

# Plans controller
from app.controllers import plans_controller
app.include_router(plans_controller.router)

# Static files
from fastapi.staticfiles import StaticFiles
import os
app_dir = os.path.dirname(__file__)
static_dir = os.path.join(app_dir, 'static')
app.mount('/static', StaticFiles(directory=static_dir), name='static')

# Session middleware
from starlette.middleware.sessions import SessionMiddleware
import os as _os
SECRET_KEY = _os.getenv('APP_SECRET_KEY') or 'dev-secret-key-change-me'
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Simple middleware: attach current user to request.state for templates and enforce UI login
from starlette.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.deps.auth import get_user_from_session
from app.db import SessionLocal
from app.models.models import User

class AttachUserAndProtectUIMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Skip auth/static/api endpoints
        if path.startswith('/auth') or path.startswith('/static') or path.startswith('/api'):
            return await call_next(request)

        # Try to read user_id from session cookie directly (do not rely on Request.session availability)
        try:
            print("DEBUG: request.cookies:", request.cookies)
            cookie_val = request.cookies.get('session')
            print("DEBUG: session_cookie:", cookie_val)
            user_id = None
            if cookie_val:
                try:
                    # SessionMiddleware uses itsdangerous.TimestampSigner over a b64-encoded JSON payload
                    from itsdangerous import TimestampSigner, BadSignature
                    import json
                    from base64 import b64decode
                    s = TimestampSigner(SECRET_KEY)
                    unsigned = s.unsign(cookie_val.encode('utf-8'))
                    payload = json.loads(b64decode(unsigned))
                    if isinstance(payload, dict):
                        user_id = payload.get('user_id')
                except Exception:
                    # Can't decode cookie; fallback to request.session if available
                    try:
                        user_id = get_user_from_session(request)
                    except Exception:
                        user_id = None
            else:
                try:
                    user_id = get_user_from_session(request)
                except Exception:
                    user_id = None
        except Exception:
            # Any unexpected error while parsing session — treat as not authenticated
            user_id = None

        if not user_id:
            # redirect to login for UI pages
            print("DEBUG: No user_id in session; redirecting to login")
            return RedirectResponse(url='/auth/login')

        # Attach full user from db to request.state for templates
        try:
            db = SessionLocal()
            from sqlalchemy.orm import joinedload
            user = db.query(User).options(joinedload(User.plan)).filter(User.id == user_id).first()
            print("DEBUG: resolved user from db:", user)
            # Access related objects while session is open to load them
            if user and user.plan:
                _ = user.plan.name  # Trigger eager load
            # Expunge user from session so it can be used after session closes
            db.expunge(user)
            request.state.user = user
        finally:
            db.close()

        return await call_next(request)

# Register middleware so it runs after SessionMiddleware
app.add_middleware(AttachUserAndProtectUIMiddleware)
print("MIDDLEWARE STACK:", [m.cls.__name__ for m in app.user_middleware])

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
