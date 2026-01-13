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
            "error_message": None,
        },
    )


@router.get("/create")
def plans_create(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "plans/create.html",
        {
            "request": request,
            "form_data": None,
            "errors": [],
        },
    )


@router.post("/create")
async def plans_create_post(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    errors = []

    form_raw = await request.form()
    payload = {
        "name": form_raw.get("name", "").strip(),
        "free_attempts_limit": form_raw.get("free_attempts_limit", "0"),
    }

    if not payload["name"]:
        errors.append("Название плана обязательно для заполнения.")

    try:
        free_attempts_limit = int(payload["free_attempts_limit"])
        if free_attempts_limit < 0:
            errors.append("Лимит попыток не может быть отрицательным.")
        payload["free_attempts_limit"] = free_attempts_limit
    except (ValueError, TypeError):
        errors.append(f"Неверный формат лимита попыток: '{payload['free_attempts_limit']}'. Ожидается число.")

    if errors:
        return templates.TemplateResponse(
            "plans/create.html",
            {
                "request": request,
                "form_data": payload,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        accessor.create_plan(payload)
    except ValueError as exc:
        errors.append(str(exc))
        return templates.TemplateResponse(
            "plans/create.html",
            {
                "request": request,
                "form_data": payload,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/plans", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{plan_id}/delete")
def plan_delete(plan_id: int, request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    try:
        accessor.delete_plan(plan_id)
        return RedirectResponse(url="/plans", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as exc:
        error_msg = str(exc)
        plans = accessor.list_plans()
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
                "error_message": error_msg,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
