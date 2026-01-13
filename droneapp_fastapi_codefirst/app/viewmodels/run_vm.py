import datetime
from typing import Optional, Literal

from fastapi import Form
from pydantic import BaseModel, ValidationError


class RunViewModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime.datetime] = None

    # Create fields
    user_id: int
    index_type: Literal["NDVI", "GNDVI"]
    status: Literal["QUEUED", "SUCCESS", "FAILED"] = "QUEUED"

    # Read-only / joined fields
    user_email: Optional[str] = None

    @classmethod
    def from_orm_run(cls, run) -> "RunViewModel":
        payload = {
            "id": run.id,
            "created_at": run.created_at,
            "user_id": run.user_id,
            "index_type": run.index_type,
            "status": run.status,
            "user_email": getattr(getattr(run, 'user', None), 'email', None),
        }
        try:
            return cls(**payload)
        except ValidationError:
            return cls.construct(**payload)

    @classmethod
    def as_form(
        cls,
        user_id: int = Form(...),
        index_type: str = Form(...),
        status: str = Form("QUEUED"),
    ) -> "RunViewModel":
        return cls(user_id=user_id, index_type=index_type, status=status)

    class Config:
        orm_mode = True
