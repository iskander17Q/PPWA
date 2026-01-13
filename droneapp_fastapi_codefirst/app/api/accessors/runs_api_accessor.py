from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.models.models import ProcessingRun, User, InputImage
from app.api.schemas.runs_dto import RunCreateDTO, RunUpdateDTO


class NotFoundError(Exception):
    pass


class RunsAPIAccessor:
    def __init__(self, db: Session):
        self.db = db

    def list_runs(self) -> List[ProcessingRun]:
        return (
            self.db.query(ProcessingRun)
            .options(joinedload(ProcessingRun.user))
            .order_by(ProcessingRun.id.desc())
            .all()
        )

    def get_run(self, run_id: int) -> Optional[ProcessingRun]:
        return (
            self.db.query(ProcessingRun)
            .options(joinedload(ProcessingRun.user))
            .filter(ProcessingRun.id == run_id)
            .first()
        )

    def create_run(self, dto: RunCreateDTO) -> ProcessingRun:
        # Validate user exists
        user = self.db.get(User, dto.user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        # Choose an input_image for the run: try to find any image for the user (newest first)
        input_image = (
            self.db.query(InputImage)
            .filter(InputImage.user_id == user.id)
            .order_by(InputImage.id.desc())
            .first()
        )
        if not input_image:
            raise ValueError("У пользователя нет загруженных изображений")

        run = ProcessingRun(
            user_id=user.id,
            input_image_id=input_image.id,
            index_type=dto.index_type.value if hasattr(dto.index_type, 'value') else dto.index_type,
            status=dto.status.value if hasattr(dto.status, 'value') else dto.status,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_run(self, run_id: int, dto: RunUpdateDTO) -> ProcessingRun:
        run = self.db.get(ProcessingRun, run_id)
        if not run:
            raise NotFoundError("Run not found")

        if dto.index_type is not None:
            run.index_type = dto.index_type.value if hasattr(dto.index_type, 'value') else dto.index_type
        if dto.status is not None:
            run.status = dto.status.value if hasattr(dto.status, 'value') else dto.status

        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
