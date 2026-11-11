from analytics import Measurement, current_status, evaluate_kpi

from .. import models, schemas


def track_strategy(
    strategy: models.Strategy, ok_threshold: float, risk_threshold: float
) -> schemas.TrackingResponse:
    items = []
    for kpi in strategy.kpis:
        results = evaluate_kpi(
            [Measurement(m.period, m.plan_value, m.fact_value) for m in kpi.measurements],
            higher_is_better=kpi.higher_is_better,
            ok_threshold=ok_threshold,
            risk_threshold=risk_threshold,
        )
        items.append(schemas.KpiTracking(
            kpi_id=kpi.id,
            name=kpi.name,
            unit=kpi.unit,
            higher_is_better=kpi.higher_is_better,
            status=current_status(results).value,
            periods=[schemas.PeriodOut(**{**r.__dict__, "status": r.status.value}) for r in results],
        ))
    return schemas.TrackingResponse(
        strategy_id=strategy.id,
        ok_threshold=ok_threshold,
        risk_threshold=risk_threshold,
        kpis=items,
    )
