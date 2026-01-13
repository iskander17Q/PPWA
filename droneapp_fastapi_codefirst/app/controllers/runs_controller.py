from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError
import traceback

from app.db import get_db
from app.accessors.runs_accessor import RunsAccessor
from app.viewmodels.run_vm import RunViewModel


templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/runs", tags=["Runs"])


def _get_accessor(db: Session) -> RunsAccessor:
    return RunsAccessor(db)


@router.get("/")
def runs_index(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    runs = accessor.list_runs_with_user()
    return templates.TemplateResponse(
        "runs/index.html",
        {
            "request": request,
            "runs": runs,
        },
    )


@router.get("/create")
def runs_create(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    users = accessor.list_users()
    return templates.TemplateResponse(
        "runs/create.html",
        {
            "request": request,
            "users": users,
            "form_data": None,
            "errors": [],
        },
    )


@router.post("/create")
async def runs_create_post(request: Request, db: Session = Depends(get_db)):
    accessor = _get_accessor(db)
    users = accessor.list_users()
    errors = []

    form_raw = await request.form()
    payload = {
        "user_id": form_raw.get("user_id"),
        "index_type": form_raw.get("index_type"),
        "status": form_raw.get("status"),
    }

    try:
        payload["user_id"] = int(payload["user_id"]) if payload["user_id"] not in (None, "") else None
        form_data = RunViewModel(**payload)
    except (ValidationError, ValueError) as e:
        error_msg = str(e)
        print(f"ERROR: Validation error when creating run: {error_msg}")
        print(f"ERROR: Payload was: {payload}")
        traceback.print_exc()
        errors.append("Проверьте корректность введённых данных (user/index_type/status).")
        return templates.TemplateResponse(
            "runs/create.html",
            {
                "request": request,
                "users": users,
                "form_data": RunViewModel.construct(**payload),
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        print(f"INFO: Creating run with data: {form_data.dict()}")
        accessor.create_run(form_data.dict())
        print(f"INFO: Run created successfully")
    except ValueError as exc:
        error_msg = str(exc)
        print(f"ERROR: ValueError when creating run: {error_msg}")
        traceback.print_exc()
        errors.append(str(exc))
        return templates.TemplateResponse(
            "runs/create.html",
            {
                "request": request,
                "users": users,
                "form_data": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except (IntegrityError, SQLAlchemyError) as exc:
        error_msg = str(exc)
        print(f"ERROR: Database error when creating run: {error_msg}")
        traceback.print_exc()
        errors.append(f"Ошибка базы данных: {error_msg}")
        return templates.TemplateResponse(
            "runs/create.html",
            {
                "request": request,
                "users": users,
                "form_data": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        error_msg = str(exc)
        print(f"ERROR: Unexpected error when creating run: {error_msg}")
        traceback.print_exc()
        errors.append(f"Неожиданная ошибка: {error_msg}")
        return templates.TemplateResponse(
            "runs/create.html",
            {
                "request": request,
                "users": users,
                "form_data": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(url="/runs", status_code=status.HTTP_303_SEE_OTHER)
