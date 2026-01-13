from typing import Optional
from fastapi import Request, HTTPException, Depends
from passlib.context import CryptContext
from app.db import get_db
from app.models.models import User
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def get_user_from_session(request: Request) -> Optional[int]:
    return request.session.get("user_id")


def get_current_user_api(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_from_session(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_from_session(request)
    if not user_id:
        return None
    return db.get(User, user_id)
