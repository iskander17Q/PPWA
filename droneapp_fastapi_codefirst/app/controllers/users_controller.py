from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.accessors.users_accessor import UsersAccessor
from app.db import get_db
from app.viewmodels.user_vm import UserViewModel

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/users", tags=["Users"])


def _get_accessor(db: Session) -> UsersAccessor:
    return UsersAccessor(db)


@router.get("/")
def users_index(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    users = accessor.list_users()
    plans = accessor.list_plans()
    return templates.TemplateResponse(
        "users/index.html",
        {
            "request": request,
            "users": users,
            "plans": plans,
            "plan_missing": len(plans) == 0,
        },
    )


@router.get("/create")
def users_create(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    plans = accessor.list_plans()
    return templates.TemplateResponse(
        "users/create.html",
        {
            "request": request,
            "plans": plans,
            "plan_missing": len(plans) == 0,
            "form_data": None,
            "errors": [],
        },
    )


@router.post("/create")
async def users_create_post(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    plans = accessor.list_plans()
    errors = []

    form_raw = await request.form()
    payload = {
        "email": form_raw.get("email", ""),
        "name": form_raw.get("name"),
        "phone": form_raw.get("phone"),
        "role": form_raw.get("role"),
        "plan_id": form_raw.get("plan_id"),
        "is_active": form_raw.get("is_active") is not None,
    }

    if not plans:
        errors.append("Нет тарифных планов. Создайте план перед добавлением пользователя.")
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "plans": plans,
                "plan_missing": True,
                "form_data": UserViewModel.construct(**payload),
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload["plan_id"] = int(payload["plan_id"]) if payload["plan_id"] not in (None, "") else None
        form_data = UserViewModel(**payload)
    except (ValidationError, ValueError):
        errors.append("Проверьте корректность введённых данных (email/role/plan).")
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "plans": plans,
                "plan_missing": False,
                "form_data": UserViewModel.construct(**payload),
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        accessor.create_user(form_data.dict())
    except ValueError as exc:
        errors.append(str(exc))
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "plans": plans,
                "plan_missing": False,
                "form_data": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{user_id}")
def user_details(user_id: int, request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    user = accessor.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return templates.TemplateResponse(
        "users/details.html",
        {"request": request, "user": user},
    )


@router.get("/{user_id}/edit")
def user_edit(user_id: int, request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    user = accessor.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    plans = accessor.list_plans()
    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "plans": plans,
            "form_data": UserViewModel.from_orm_user(user),
            "errors": [],
        },
    )


@router.post("/{user_id}/edit")
async def user_edit_post(user_id: int, request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    plans = accessor.list_plans()
    errors = []

    user = accessor.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    form_raw = await request.form()
    payload = {
        "email": form_raw.get("email", ""),
        "name": form_raw.get("name"),
        "phone": form_raw.get("phone"),
        "role": form_raw.get("role"),
        "plan_id": form_raw.get("plan_id"),
        "is_active": form_raw.get("is_active") is not None,
    }

    try:
        payload["plan_id"] = int(payload["plan_id"]) if payload["plan_id"] not in (None, "") else None
        form_data = UserViewModel(**payload)
    except (ValidationError, ValueError):
        errors.append("Проверьте корректность введённых данных (email/role/plan).")
        return templates.TemplateResponse(
            "users/edit.html",
            {
                "request": request,
                "plans": plans,
                "form_data": UserViewModel.construct(
                    id=user.id,
                    created_at=user.created_at,
                    free_attempts_used=user.free_attempts_used,
                    **payload,
                ),
                "errors": errors,
                "user_id": user_id,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Enrich form data with readonly fields for the template
    form_data.id = user.id
    form_data.created_at = user.created_at
    form_data.free_attempts_used = user.free_attempts_used

    try:
        accessor.update_user(user_id, form_data.dict())
    except ValueError as exc:
        errors.append(str(exc))
        return templates.TemplateResponse(
            "users/edit.html",
            {
                "request": request,
                "plans": plans,
                "form_data": form_data,
                "errors": errors,
                "user_id": user_id,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url=f"/users/{user_id}", status_code=status.HTTP_303_SEE_OTHER)
