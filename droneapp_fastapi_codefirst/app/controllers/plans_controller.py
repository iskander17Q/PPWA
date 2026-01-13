from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.accessors.users_accessor import UsersAccessor
from app.db import get_db

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/plans", tags=["Plans"])


def _get_accessor(db: Session) -> UsersAccessor:
    return UsersAccessor(db)


@router.get("/")
def plans_index(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    plans = accessor.list_plans()
    
    # Get user count for each plan
    from app.models.models import User
    plan_stats = {}
    for plan in plans:
        user_count = db.query(User).filter(User.plan_id == plan.id).count()
        plan_stats[plan.id] = user_count
    
    return templates.TemplateResponse(
        "plans/index.html",
        {
            "request": request,
            "plans": plans,
            "plan_stats": plan_stats,
        },
    )
