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
        # Convert plan_id to int, handling string input
        plan_id_str = payload.get("plan_id")
        if plan_id_str is not None and plan_id_str != "":
            try:
                payload["plan_id"] = int(plan_id_str)
            except (ValueError, TypeError):
                errors.append(f"Неверный формат тарифа: '{plan_id_str}'. Ожидается число.")
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
        else:
            errors.append("Тариф обязателен для заполнения.")
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
        
        # Validate with Pydantic
        form_data = UserViewModel(**payload)
    except ValidationError as e:
        # Extract detailed validation errors
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0]
            msg = error.get("msg", "Ошибка валидации")
            errors.append(f"Поле '{field}': {msg}")
        # Also add generic message
        if not errors:
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
    except (ValueError, TypeError) as e:
        errors.append(f"Ошибка обработки данных: {str(e)}")
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
        error_msg = str(exc)
        errors.append(error_msg)
        
        # If user already exists, try to find them and suggest editing
        existing_user = None
        if "уже существует" in error_msg.lower() or "already exists" in error_msg.lower():
            # Try to extract user ID from error message or search by email
            import re
            id_match = re.search(r'ID:\s*(\d+)', error_msg)
            if id_match:
                user_id = int(id_match.group(1))
                existing_user = accessor.get_user(user_id)
            else:
                # Fallback: search by email (normalized)
                email_normalized = str(form_data.email).strip().lower()
                existing_user = accessor.get_user_by_email(email_normalized)
        
        return templates.TemplateResponse(
            "users/create.html",
            {
                "request": request,
                "plans": plans,
                "plan_missing": False,
                "form_data": form_data,
                "errors": errors,
                "existing_user": existing_user,
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
        # Convert plan_id to int, handling string input
        plan_id_str = payload.get("plan_id")
        if plan_id_str is not None and plan_id_str != "":
            try:
                payload["plan_id"] = int(plan_id_str)
            except (ValueError, TypeError):
                errors.append(f"Неверный формат тарифа: '{plan_id_str}'. Ожидается число.")
                payload["plan_id"] = user.plan_id  # Fallback to current plan
        else:
            errors.append("Тариф обязателен для заполнения.")
            payload["plan_id"] = user.plan_id  # Fallback to current plan
        
        # Validate with Pydantic
        form_data = UserViewModel(**payload)
    except ValidationError as e:
        # Extract detailed validation errors
        for error in e.errors():
            field = error.get("loc", ["unknown"])[0]
            msg = error.get("msg", "Ошибка валидации")
            errors.append(f"Поле '{field}': {msg}")
        # Also add generic message
        if not errors:
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
    except (ValueError, TypeError) as e:
        errors.append(f"Ошибка обработки данных: {str(e)}")
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
        updated_user = accessor.update_user(user_id, form_data.dict())
        # If current user updated their own plan, refresh session data
        if hasattr(request.state, 'user') and request.state.user and request.state.user.id == user_id:
            # Reload user with plan relationship for session
            from sqlalchemy.orm import joinedload
            from app.models.models import User as UserModel
            refreshed_user = db.query(UserModel).options(joinedload(UserModel.plan)).filter(UserModel.id == user_id).first()
            if refreshed_user:
                # Access plan to trigger eager load before session closes
                if refreshed_user.plan:
                    _ = refreshed_user.plan.name
                db.expunge(refreshed_user)
                request.state.user = refreshed_user
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
