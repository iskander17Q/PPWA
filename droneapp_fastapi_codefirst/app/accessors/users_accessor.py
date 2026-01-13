from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from app.models.models import User, SubscriptionPlan


class UsersAccessor:
    def __init__(self, db: Session):
        self.db = db

    def list_users(self) -> List[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.plan))
            .order_by(User.id)
            .all()
        )

    def list_users_with_runs_eager(self) -> List[User]:
        # Use selectinload to eager load processing_runs
        return self.db.query(User).options(selectinload(User.processing_runs)).order_by(User.id).all()

    def list_plans(self) -> List[SubscriptionPlan]:
        return self.db.query(SubscriptionPlan).order_by(SubscriptionPlan.name).all()

    def get_user(self, user_id: int) -> Optional[User]:
        return (
            self.db.query(User)
            .options(joinedload(User.plan))
            .filter(User.id == user_id)
            .first()
        )

    def get_user_by_email(self, email: str) -> Optional[User]:
        # Normalize email for search: trim and lowercase
        email_normalized = str(email).strip().lower()
        # Try exact match first
        user = (
            self.db.query(User)
            .options(joinedload(User.plan))
            .filter(User.email == email_normalized)
            .first()
        )
        if user:
            return user
        # Fallback: case-insensitive search (for existing data)
        return (
            self.db.query(User)
            .options(joinedload(User.plan))
            .filter(User.email.ilike(email_normalized))
            .first()
        )

    def _ensure_plan(self, plan_id: int) -> SubscriptionPlan:
        plan = self.db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError("Указанный тарифный план не найден")
        return plan

    def create_user(self, data: Dict[str, Any]) -> User:
        # Normalize email: trim and lowercase
        email = str(data["email"]).strip().lower()
        
        # Check if user with this email already exists
        existing = self.get_user_by_email(email)
        if existing:
            raise ValueError(f"Пользователь с email '{email}' уже существует (ID: {existing.id})")
        
        self._ensure_plan(data["plan_id"])
        
        # For SQLite, we need to generate ID manually if using BigInteger
        # Get the next available ID
        max_id = self.db.query(User.id).order_by(User.id.desc()).first()
        next_id = (max_id[0] + 1) if max_id else 1
        
        user = User(
            id=next_id,  # Explicitly set ID for SQLite
            email=email,
            name=data.get("name"),
            phone=data.get("phone"),
            role=data["role"],
            plan_id=data["plan_id"],
            is_active=data.get("is_active", True),
            password_hash="fakehash",
            free_attempts_used=data.get("free_attempts_used", 0),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            # Try to find the conflicting user
            conflicting = self.get_user_by_email(email)
            if conflicting:
                raise ValueError(f"Пользователь с email '{email}' уже существует (ID: {conflicting.id})") from exc
            else:
                raise ValueError(f"Ошибка при создании пользователя: {str(exc)}") from exc
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        user = self.get_user(user_id)
        if not user:
            return None

        self._ensure_plan(data["plan_id"])
        user.email = data["email"]
        user.name = data.get("name")
        user.phone = data.get("phone")
        user.role = data["role"]
        user.plan_id = data["plan_id"]
        user.is_active = data.get("is_active", True)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ValueError("Пользователь с таким email уже существует") from exc
        self.db.refresh(user)
        return user
