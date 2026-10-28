"""Этап 1: отсев неэффективных проектов по порогу агрегированного показателя AP."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ProjectScore:
    id: int
    name: str
    ap: float


@dataclass
class ScreeningResult:
    accepted: list[ProjectScore] = field(default_factory=list)
    rejected: list[ProjectScore] = field(default_factory=list)


def screen_projects(projects: Iterable[ProjectScore], threshold: float) -> ScreeningResult:
    """Проект проходит отсев, если AP >= threshold. Порядок проектов сохраняется."""
    if not math.isfinite(threshold):
        raise ValueError("threshold должен быть конечным числом")

    result = ScreeningResult()
    for p in projects:
        if not math.isfinite(p.ap):
            raise ValueError(f"Некорректное значение AP у проекта {p.id}: {p.ap}")
        (result.accepted if p.ap >= threshold else result.rejected).append(p)
    return result
