"""Связывает БД и расчётное ядро: читает проекты, вызывает analytics, формирует ответ."""
from sqlalchemy.orm import Session

from analytics import ProjectScore, screen_projects

from .. import models, schemas


def evaluate_strategy(db: Session, strategy: models.Strategy, threshold: float) -> schemas.EvaluateResponse:
    projects = {p.id: p for p in strategy.projects}
    scores = [ProjectScore(id=p.id, name=p.name, ap=p.ap) for p in projects.values()]

    result = screen_projects(scores, threshold)

    return schemas.EvaluateResponse(
        strategy_id=strategy.id,
        threshold=threshold,
        accepted=[schemas.ProjectOut.model_validate(projects[s.id]) for s in result.accepted],
        rejected=[schemas.ProjectOut.model_validate(projects[s.id]) for s in result.rejected],
    )
