import datetime
import re
from typing import Optional, Literal

from fastapi import Form
from pydantic import BaseModel, ValidationError, validator


class UserViewModel(BaseModel):
    id: Optional[int] = None
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Literal["USER", "ADMIN"]
    plan_id: int
    is_active: bool = True
    created_at: Optional[datetime.datetime] = None
    free_attempts_used: int = 0

    @validator("email", pre=True)
    def validate_email(cls, value):
        if not value:
            raise ValueError("Email обязателен для заполнения")
        value = str(value).strip()
        # More lenient email validation that allows .local domains
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError("Неверный формат email")
        return value

    @validator("name", "phone", pre=True)
    def empty_to_none(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        return value or None

    @classmethod
    def from_orm_user(cls, user) -> "UserViewModel":
        payload = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "plan_id": user.plan_id,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "free_attempts_used": user.free_attempts_used,
        }
        try:
            return cls(**payload)
        except ValidationError:
            # Допускаем существующие "грязные" данные в БД, чтобы форма могла отобразиться.
            return cls.construct(**payload)

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        name: Optional[str] = Form(""),
        phone: Optional[str] = Form(""),
        role: str = Form(...),
        plan_id: int = Form(...),
        is_active: bool = Form(False),
    ) -> "UserViewModel":
        return cls(
            email=email,
            name=name,
            phone=phone,
            role=role,
            plan_id=plan_id,
            is_active=is_active,
        )

    class Config:
        orm_mode = True
