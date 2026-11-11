"""Отслеживание эффективности: сравнение плана и факта по показателю (KPI).

Чистые функции, без БД и HTTP.

Выполнение плана (completion_pct):
  * чем больше, тем лучше:  факт / план * 100
  * чем меньше, тем лучше:  план / факт * 100
Значение выше 100 означает перевыполнение. Пороги статусов (ok_threshold,
risk_threshold) заданы по умолчанию условно и должны быть уточнены.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class Status(str, Enum):
    ON_TRACK = "on_track"      # в норме
    AT_RISK = "at_risk"        # риск отставания
    OFF_TRACK = "off_track"    # отставание
    NO_DATA = "no_data"        # факта ещё нет


@dataclass(frozen=True)
class Measurement:
    period: str
    plan: float
    fact: Optional[float]


@dataclass(frozen=True)
class PeriodResult:
    period: str
    plan: float
    fact: Optional[float]
    deviation: Optional[float]        # факт - план
    completion_pct: Optional[float]
    status: Status


def completion_pct(plan: float, fact: float, higher_is_better: bool = True) -> float:
    if higher_is_better:
        if plan == 0:
            return 100.0 if fact >= 0 else 0.0
        return fact / plan * 100.0
    # меньше - лучше
    if fact == 0:
        return 100.0
    if plan == 0:
        return 0.0
    return plan / fact * 100.0


def classify(pct: float, ok_threshold: float, risk_threshold: float) -> Status:
    if pct >= ok_threshold:
        return Status.ON_TRACK
    if pct >= risk_threshold:
        return Status.AT_RISK
    return Status.OFF_TRACK


def evaluate_kpi(
    measurements: Iterable[Measurement],
    higher_is_better: bool = True,
    ok_threshold: float = 95.0,
    risk_threshold: float = 80.0,
) -> list[PeriodResult]:
    """Оценивает показатель по периодам. Результат отсортирован по периоду."""
    if not (0 <= risk_threshold <= ok_threshold):
        raise ValueError("Должно выполняться 0 <= risk_threshold <= ok_threshold")

    results: list[PeriodResult] = []
    for m in sorted(measurements, key=lambda x: x.period):
        if not math.isfinite(m.plan) or (m.fact is not None and not math.isfinite(m.fact)):
            raise ValueError(f"Некорректное значение в периоде {m.period}")
        if m.fact is None:
            results.append(PeriodResult(m.period, m.plan, None, None, None, Status.NO_DATA))
            continue
        pct = completion_pct(m.plan, m.fact, higher_is_better)
        results.append(
            PeriodResult(
                period=m.period,
                plan=m.plan,
                fact=m.fact,
                deviation=m.fact - m.plan,
                completion_pct=round(pct, 2),
                status=classify(pct, ok_threshold, risk_threshold),
            )
        )
    return results


def current_status(results: list[PeriodResult]) -> Status:
    """Статус показателя = статус последнего периода, в котором есть факт."""
    for r in reversed(results):
        if r.status is not Status.NO_DATA:
            return r.status
    return Status.NO_DATA
