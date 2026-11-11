from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    projects: Mapped[list["Project"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )
    kpis: Mapped[list["Kpi"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan", order_by="Kpi.id"
    )


class Project(Base):
    """Паспорт проекта. Пока хранит только готовое значение AP."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    ap: Mapped[float] = mapped_column(Float, default=0.0)

    strategy: Mapped[Strategy] = relationship(back_populates="projects")


class Kpi(Base):
    """Показатель эффективности стратегии."""

    __tablename__ = "kpis"
    __table_args__ = (UniqueConstraint("strategy_id", "name", name="uq_kpi_strategy_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(50), default="")
    higher_is_better: Mapped[bool] = mapped_column(Boolean, default=True)

    strategy: Mapped[Strategy] = relationship(back_populates="kpis")
    measurements: Mapped[list["KpiMeasurement"]] = relationship(
        back_populates="kpi", cascade="all, delete-orphan", order_by="KpiMeasurement.period"
    )


class KpiMeasurement(Base):
    """План и факт показателя за период (например, 2026-01 или 2026-Q1)."""

    __tablename__ = "kpi_measurements"
    __table_args__ = (UniqueConstraint("kpi_id", "period", name="uq_measurement_kpi_period"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    kpi_id: Mapped[int] = mapped_column(ForeignKey("kpis.id", ondelete="CASCADE"))
    period: Mapped[str] = mapped_column(String(20))
    plan_value: Mapped[float] = mapped_column(Float)
    fact_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    kpi: Mapped[Kpi] = relationship(back_populates="measurements")
