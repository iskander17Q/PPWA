from sqlalchemy.orm import Session
from typing import List
from app.models.db_models import ProcessingRuns as ProcessingRun


class RunsAccessor:
    def __init__(self, db: Session):
        self.db = db

    def list_runs(self) -> List[ProcessingRun]:
        """Return processing runs ordered by id descending."""
        return self.db.query(ProcessingRun).order_by(ProcessingRun.id.desc()).all()
