from __future__ import annotations
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class IndexType(str, Enum):
    NDVI = "NDVI"
    GNDVI = "GNDVI"


class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class RunReadDTO(BaseModel):
    id: int
    user_id: int
    user_email: Optional[str]
    index_type: IndexType
    status: RunStatus
    created_at: datetime

    class Config:
        orm_mode = True


class RunCreateDTO(BaseModel):
    user_id: int
    index_type: IndexType
    status: RunStatus = RunStatus.QUEUED


class RunUpdateDTO(BaseModel):
    index_type: Optional[IndexType] = None
    status: Optional[RunStatus] = None
