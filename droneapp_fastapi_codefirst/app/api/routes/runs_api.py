from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.api.accessors.runs_api_accessor import RunsAPIAccessor, NotFoundError
from app.api.mappers.run_mapper import map_run_to_dto
from app.api.schemas.runs_dto import RunReadDTO, RunCreateDTO, RunUpdateDTO

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/", response_model=List[RunReadDTO])
def list_runs(db: Session = Depends(get_db)):
    accessor = RunsAPIAccessor(db)
    runs = accessor.list_runs()
    return [map_run_to_dto(r) for r in runs]


@router.get("/{run_id}", response_model=RunReadDTO)
def get_run(run_id: int, db: Session = Depends(get_db)):
    accessor = RunsAPIAccessor(db)
    run = accessor.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return map_run_to_dto(run)


@router.post("/", response_model=RunReadDTO, status_code=status.HTTP_201_CREATED)
def create_run(dto: RunCreateDTO, db: Session = Depends(get_db)):
    accessor = RunsAPIAccessor(db)
    try:
        run = accessor.create_run(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return map_run_to_dto(run)


@router.put("/{run_id}", response_model=RunReadDTO)
def update_run(run_id: int, dto: RunUpdateDTO, db: Session = Depends(get_db)):
    accessor = RunsAPIAccessor(db)
    try:
        run = accessor.update_run(run_id, dto)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return map_run_to_dto(run)
