from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
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


class Project(Base):
    """Паспорт проекта. Пока хранит только готовое значение AP."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    ap: Mapped[float] = mapped_column(Float, default=0.0)

    strategy: Mapped[Strategy] = relationship(back_populates="projects")
