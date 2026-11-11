from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..importers.measurements import ImportFileError, parse_measurements
from ..services.evaluation import evaluate_strategy
from ..services.importing import import_rows
from ..services.tracking import track_strategy

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _get_strategy(db: Session, strategy_id: int) -> models.Strategy:
    strategy = db.get(models.Strategy, strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Стратегия не найдена")
    return strategy


@router.post("", response_model=schemas.StrategyOut, status_code=201)
def create_strategy(data: schemas.StrategyCreate, db: Session = Depends(get_db)):
    strategy = models.Strategy(**data.model_dump())
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("", response_model=list[schemas.StrategyOut])
def list_strategies(db: Session = Depends(get_db)):
    return db.scalars(select(models.Strategy).order_by(models.Strategy.id)).all()


@router.post("/{strategy_id}/projects", response_model=schemas.ProjectOut, status_code=201)
def add_project(strategy_id: int, data: schemas.ProjectCreate, db: Session = Depends(get_db)):
    strategy = _get_strategy(db, strategy_id)
    project = models.Project(strategy_id=strategy.id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{strategy_id}/projects", response_model=list[schemas.ProjectOut])
def list_projects(strategy_id: int, db: Session = Depends(get_db)):
    return _get_strategy(db, strategy_id).projects


@router.post("/{strategy_id}/evaluate", response_model=schemas.EvaluateResponse)
def evaluate(strategy_id: int, data: schemas.EvaluateRequest, db: Session = Depends(get_db)):
    strategy = _get_strategy(db, strategy_id)
    return evaluate_strategy(db, strategy, data.threshold)


MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.post("/{strategy_id}/import", response_model=schemas.ImportSummary)
async def import_measurements(
    strategy_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Загрузка плана и факта показателей из CSV или XLSX."""
    strategy = _get_strategy(db, strategy_id)
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 5 МБ")
    try:
        rows = parse_measurements(file.filename or "", content)
    except ImportFileError as exc:
        raise HTTPException(status_code=422, detail=exc.errors)
    return import_rows(db, strategy, rows)


@router.get("/{strategy_id}/tracking", response_model=schemas.TrackingResponse)
def tracking(
    strategy_id: int,
    ok_threshold: float = Query(95.0, ge=0, allow_inf_nan=False),
    risk_threshold: float = Query(80.0, ge=0, allow_inf_nan=False),
    db: Session = Depends(get_db),
):
    """План/факт по показателям: отклонения, выполнение, статусы."""
    if risk_threshold > ok_threshold:
        raise HTTPException(status_code=422, detail="risk_threshold не может быть больше ok_threshold")
    return track_strategy(_get_strategy(db, strategy_id), ok_threshold, risk_threshold)
