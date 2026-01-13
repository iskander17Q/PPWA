from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import List
import traceback
from app.models.models import ProcessingRun, User, InputImage


class RunsAccessor:
    def __init__(self, db: Session):
        self.db = db

    def list_runs(self) -> List[ProcessingRun]:
        return self.db.query(ProcessingRun).order_by(ProcessingRun.id.desc()).all()

    def list_runs_with_user(self) -> List[ProcessingRun]:
        # Eager load user to access user.email in templates without N+1
        return (
            self.db.query(ProcessingRun)
            .options(joinedload(ProcessingRun.user))
            .order_by(ProcessingRun.id.desc())
            .all()
        )

    def create_run(self, data: dict) -> ProcessingRun:
        # Validate user exists
        user = self.db.get(User, data.get("user_id"))
        if not user:
            raise ValueError("Пользователь не найден")

        # Choose an input_image for the run: try to find any image for the user
        input_image = (
            self.db.query(InputImage)
            .filter(InputImage.user_id == user.id)
            .order_by(InputImage.id)
            .first()
        )
        if not input_image:
            raise ValueError("У пользователя нет загруженных изображений. Сначала добавьте InputImage.")

        run = ProcessingRun(
            user_id=user.id,
            input_image_id=input_image.id,
            index_type=data.get("index_type"),
            status=data.get("status", "QUEUED"),
        )
        try:
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)
            print(f"INFO: Successfully created run ID={run.id} for user_id={user.id}")
            return run
        except IntegrityError as e:
            self.db.rollback()
            print(f"ERROR: IntegrityError when creating run: {e}")
            traceback.print_exc()
            raise ValueError(f"Ошибка сохранения: {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"ERROR: SQLAlchemyError when creating run: {e}")
            traceback.print_exc()
            raise ValueError(f"Ошибка базы данных: {str(e)}")

    def list_users(self) -> List[User]:
        return self.db.query(User).order_by(User.id).all()
