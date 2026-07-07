"""Contratos internos dos agentes (structured outputs auditáveis)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChecklistFinding(BaseModel):
    dimension: str
    item: str
    status: str  # atende | parcial | nao_atende | nao_aplicavel | a_validar
    evidence: str
    priority: str = "media"  # alta | media | baixa


class RecommendationFinding(BaseModel):
    component: str | None = None
    barrier: str
    impact: str | None = None
    option_min: str | None = None
    option_mid: str | None = None
    option_premium: str | None = None
    effort: str = "medio"
    priority: str = "media"
    evidence_level: str = "heuristica"  # heuristica | evidencia | a_validar
    standard_ref: str | None = None
    standard_status: str | None = None  # confirmada | referencia_design | hipotese | ...


class DimensionScore(BaseModel):
    dimension: str
    weight: int
    score: float  # 0..100 na dimensão


class TraceRecord(BaseModel):
    agent_name: str
    input_summary: str = ""
    output_summary: str = ""
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0


class AnalysisResult(BaseModel):
    engine: str
    model_used: str | None = None
    checklist: list[ChecklistFinding] = Field(default_factory=list)
    recommendations: list[RecommendationFinding] = Field(default_factory=list)
    dimensions: list[DimensionScore] = Field(default_factory=list)
    score_total: float = 0.0
    maturity_level: str = "Crítico"
    gate: str = "vermelho"
    traces: list[TraceRecord] = Field(default_factory=list)
