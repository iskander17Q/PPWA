from sqlalchemy.orm import Session
from typing import List
from app.models.db_models import Users as User


class UsersAccessor:
    def __init__(self, db: Session):
        self.db = db

    def list_users(self) -> List[User]:
        """Return all users ordered by id ascending."""
        return self.db.query(User).order_by(User.id).all()
