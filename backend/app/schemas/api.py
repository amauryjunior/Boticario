"""Contratos de entrada/saída da API (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class SignupIn(BaseModel):
    organization_name: str
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str
    organization_id: str


# ---------- Projeto / Produto ----------
class ProjectIn(BaseModel):
    name: str
    objective: str | None = None
    target_market: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    objective: str | None
    target_market: str | None
    status: str
    created_at: datetime


class ComponentIn(BaseModel):
    component_type: str
    material: str | None = None
    dimensions: str | None = None
    description: str | None = None


class ProductIn(BaseModel):
    project_id: str
    name: str
    brand: str | None = None
    category: str | None = None
    description: str | None = None
    target_user: str | None = None
    country: str | None = "BR"
    lifecycle_stage: str | None = None
    cap_type: str | None = None
    components: list[ComponentIn] = []


class ComponentOut(ComponentIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    file_url: str
    image_type: str | None
    uploaded_at: datetime


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    brand: str | None
    category: str | None
    description: str | None
    cap_type: str | None
    components: list[ComponentOut] = []
    images: list[ImageOut] = []


# ---------- Análise ----------
class AnalysisRunIn(BaseModel):
    product_id: str
    profiles: list[str] = Field(
        default_factory=lambda: ["baixa_visao", "destreza_reduzida"],
        description="Perfis de necessidade a considerar (RF-009).",
    )


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    dimension: str
    item: str
    status: str
    evidence: str | None
    priority: str | None


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    component: str | None
    barrier: str
    impact: str | None
    option_min: str | None
    option_mid: str | None
    option_premium: str | None
    effort: str | None
    priority: str | None
    evidence_level: str | None
    standard_ref: str | None
    standard_status: str | None
    norm_evidence: str | None = None


class ScoreDimension(BaseModel):
    dimension: str
    weight: int
    score: float


class AnalysisRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    status: str
    score_total: float | None
    maturity_level: str | None
    engine: str | None
    model_used: str | None
    started_at: datetime
    finished_at: datetime | None


class ScoreOut(BaseModel):
    score_total: float
    maturity_level: str
    gate: str
    dimensions: list[ScoreDimension]


class TraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    agent_name: str
    input_summary: str | None
    output_summary: str | None
    tokens_used: int
    cost: float
    latency_ms: int


class UsageOut(BaseModel):
    total_analyses: int
    total_tokens: int
    total_cost_usd: float
    avg_cost_per_analysis_usd: float
    avg_latency_ms: float
    by_agent: list[dict]


class ReportIn(BaseModel):
    analysis_run_id: str
    format: str = "json"


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    analysis_run_id: str
    format: str
    version: int
    content: str | None
    created_at: datetime
