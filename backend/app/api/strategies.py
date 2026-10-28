from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from ..services.evaluation import evaluate_strategy

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
