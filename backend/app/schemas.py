from pydantic import BaseModel, ConfigDict, Field


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""


class StrategyOut(StrategyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    ap: float = Field(allow_inf_nan=False)


class ProjectOut(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    strategy_id: int


class EvaluateRequest(BaseModel):
    threshold: float = Field(allow_inf_nan=False)


class EvaluateResponse(BaseModel):
    strategy_id: int
    threshold: float
    accepted: list[ProjectOut]
    rejected: list[ProjectOut]


class ImportSummary(BaseModel):
    kpis_created: int
    measurements_created: int
    measurements_updated: int


class PeriodOut(BaseModel):
    period: str
    plan: float
    fact: float | None
    deviation: float | None
    completion_pct: float | None
    status: str


class KpiTracking(BaseModel):
    kpi_id: int
    name: str
    unit: str
    higher_is_better: bool
    status: str
    periods: list[PeriodOut]


class TrackingResponse(BaseModel):
    strategy_id: int
    ok_threshold: float
    risk_threshold: float
    kpis: list[KpiTracking]
