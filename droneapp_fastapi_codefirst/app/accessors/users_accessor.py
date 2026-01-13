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

    def _ensure_plan(self, plan_id: int) -> SubscriptionPlan:
        plan = self.db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise ValueError("Указанный тарифный план не найден")
        return plan

    def create_user(self, data: Dict[str, Any]) -> User:
        self._ensure_plan(data["plan_id"])
        user = User(
            email=data["email"],
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
            raise ValueError("Пользователь с таким email уже существует") from exc
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
