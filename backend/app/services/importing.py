from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..importers.measurements import ImportRow


def import_rows(db: Session, strategy: models.Strategy, rows: list[ImportRow]) -> schemas.ImportSummary:
    """Создаёт недостающие показатели и добавляет или обновляет измерения. Всё в одной транзакции."""
    kpis = {k.name: k for k in strategy.kpis}
    created_kpis = created = updated = 0

    for row in rows:
        kpi = kpis.get(row.kpi)
        if kpi is None:
            kpi = models.Kpi(
                strategy_id=strategy.id,
                name=row.kpi,
                unit=row.unit,
                higher_is_better=True if row.higher_is_better is None else row.higher_is_better,
            )
            db.add(kpi)
            db.flush()
            kpis[row.kpi] = kpi
            created_kpis += 1
        else:
            if row.unit:
                kpi.unit = row.unit
            if row.higher_is_better is not None:
                kpi.higher_is_better = row.higher_is_better

        m = db.scalar(
            select(models.KpiMeasurement).where(
                models.KpiMeasurement.kpi_id == kpi.id,
                models.KpiMeasurement.period == row.period,
            )
        )
        if m is None:
            db.add(models.KpiMeasurement(
                kpi_id=kpi.id, period=row.period, plan_value=row.plan, fact_value=row.fact))
            created += 1
        else:
            m.plan_value = row.plan
            m.fact_value = row.fact
            updated += 1

    db.commit()
    return schemas.ImportSummary(
        kpis_created=created_kpis, measurements_created=created, measurements_updated=updated)
