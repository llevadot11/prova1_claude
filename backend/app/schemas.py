from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Mode = Literal["default", "familiar", "runner", "movilidad_reducida"]
Family = Literal["trafico", "accidentes", "aire", "meteo", "sensibilidad"]


class FamilyContribution(BaseModel):
    family: Family
    score: float = Field(ge=0, le=1, description="Score 0-1 de la familia")
    weight: float = Field(ge=0, le=1, description="Peso aplicado por el modo")
    contribution_pct: float = Field(ge=0, le=100, description="% del UFI que aporta")


class BarrioUFI(BaseModel):
    barrio_id: str
    barrio_name: str
    district_name: str = ""
    ufi: float = Field(ge=0, le=100)
    contribuciones: list[FamilyContribution]


class UFIResponse(BaseModel):
    at: datetime
    mode: Mode
    barrios: list[BarrioUFI]


class TramoState(BaseModel):
    tram_id: int
    state: int = Field(ge=1, le=6, description="estatActual TRAMS: 1=fluido…6=cortado")


class TramosStateResponse(BaseModel):
    at: datetime
    tramos: list[TramoState]


class BarrioDetail(BaseModel):
    barrio_id: str
    barrio_name: str
    district_name: str = ""
    at: datetime
    mode: Mode
    ufi: float
    contribuciones: list[FamilyContribution]
    raw: dict[str, float | int | str | None] = Field(
        default_factory=dict,
        description="Valores crudos: temp, precip, pm2_5, NO2, estat_medio_tramos, etc.",
    )


class ExplainResponse(BaseModel):
    barrio_id: str
    at: datetime
    mode: Mode
    text: str
    cached: bool


class ModePreset(BaseModel):
    id: Mode
    label: str
    description: str
    weights: dict[Family, float]


class HealthStatus(BaseModel):
    api: Literal["ok", "degraded", "down"]
    open_meteo: Literal["ok", "degraded", "down", "unknown"]
    open_meteo_aq: Literal["ok", "degraded", "down", "unknown"]
    anthropic: Literal["ok", "degraded", "down", "unknown"]
    demo_offline: bool
    ufi_parquet_age_seconds: int | None
