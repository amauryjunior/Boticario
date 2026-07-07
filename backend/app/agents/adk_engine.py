"""Motor de análise com Google ADK + Gemini/Vertex AI.

Ativado quando ANALYSIS_ENGINE=adk e o pacote google-adk está instalado e
configurado (Vertex AI ou GOOGLE_API_KEY). Constrói a malha de agentes descrita
em docs/inclua-beauty/01-arquitetura-gcp-adk.md. Em caso de indisponibilidade,
levanta exceção e o runner faz fallback para o motor heurístico.
"""
from __future__ import annotations

import json
import os
import time

from pydantic import BaseModel

from app.agents.schemas import (
    AnalysisResult,
    ChecklistFinding,
    RecommendationFinding,
    TraceRecord,
)
from app.agents.scoring import approval_gate, compute_scores, maturity_level
from app.core.config import settings

# Preços de referência por 1M tokens (USD). Ajustar aos valores vigentes do GCP.
_PRICE = {
    "flash": {"in": 0.15 / 1_000_000, "out": 0.60 / 1_000_000},
    "pro": {"in": 1.25 / 1_000_000, "out": 5.00 / 1_000_000},
}


class _LlmChecklist(BaseModel):
    dimension: str
    item: str
    status: str
    evidence: str
    priority: str = "media"


class _LlmRec(BaseModel):
    component: str | None = None
    barrier: str
    impact: str | None = None
    option_min: str | None = None
    option_mid: str | None = None
    option_premium: str | None = None
    standard_ref: str | None = None
    standard_status: str | None = None


class _LlmAnalysis(BaseModel):
    checklist: list[_LlmChecklist]
    recommendations: list[_LlmRec]


_INSTRUCTION = """
Você é a malha de agentes de acessibilidade da Inclua Beauty. Analise a
embalagem de beleza descrita (JSON) para os perfis de necessidade informados.

Dimensões de checklist válidas: "Operabilidade e abertura",
"Identificação tátil e multisensorial", "Leitura, contraste e rotulagem",
"Clareza das instruções", "Segurança e risco de uso incorreto",
"Sustentabilidade e refil", "Inovação inclusiva", "Evidência/teste com usuário".

status válido: atende | parcial | nao_atende | nao_aplicavel | a_validar.
priority: alta | media | baixa.

Regras obrigatórias:
- Nunca afirme conformidade legal definitiva; ao citar norma, informe
  standard_status (confirmada | aplicavel_com_ressalva | referencia_design |
  hipotese | pendente_validacao).
- Use linguagem não capacitista.
- Para cada barreira, ofereça 3 alternativas (mínima, intermediária, premium).
Responda estritamente no schema estruturado.
"""


def _configure_env() -> None:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", settings.google_genai_use_vertexai)
    if settings.google_cloud_project:
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", settings.google_cloud_project)
    if settings.google_cloud_location:
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.google_cloud_location)
    if settings.google_api_key:
        os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)


def available() -> bool:
    try:
        import google.adk  # noqa: F401
    except Exception:
        return False
    return bool(
        settings.google_api_key
        or settings.google_genai_use_vertexai.upper() == "TRUE"
    )


def analyze(product: dict, profiles: list[str]) -> AnalysisResult:
    """Executa o orquestrador ADK. Levanta exceção se algo falhar (runner faz fallback)."""
    _configure_env()
    t0 = time.perf_counter()

    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.genai import types  # type: ignore

    orchestrator = LlmAgent(
        name="InclusaBeautyOrchestrator",
        model=settings.model_pro,
        instruction=_INSTRUCTION,
        output_schema=_LlmAnalysis,
        output_key="analysis",
    )

    runner = InMemoryRunner(agent=orchestrator, app_name="inclua-beauty")
    session = runner.session_service.create_session_sync(
        app_name="inclua-beauty", user_id="system"
    )
    payload = json.dumps({"product": product, "profiles": profiles}, ensure_ascii=False)
    message = types.Content(role="user", parts=[types.Part(text=payload)])

    final_text = ""
    tokens_in = tokens_out = 0
    for event in runner.run(
        user_id="system", session_id=session.id, new_message=message
    ):
        if getattr(event, "usage_metadata", None):
            tokens_in += getattr(event.usage_metadata, "prompt_token_count", 0) or 0
            tokens_out += getattr(event.usage_metadata, "candidates_token_count", 0) or 0
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    parsed = _LlmAnalysis.model_validate_json(final_text)
    checklist = [ChecklistFinding(**c.model_dump()) for c in parsed.checklist]
    recs = [
        RecommendationFinding(evidence_level="a_validar", **r.model_dump())
        for r in parsed.recommendations
    ]

    dims, total = compute_scores(checklist)
    price = _PRICE["pro"]
    cost = tokens_in * price["in"] + tokens_out * price["out"]
    latency = int((time.perf_counter() - t0) * 1000)

    return AnalysisResult(
        engine="adk",
        model_used=settings.model_pro,
        checklist=checklist,
        recommendations=recs,
        dimensions=dims,
        score_total=total,
        maturity_level=maturity_level(total),
        gate=approval_gate(total, checklist),
        traces=[TraceRecord(
            agent_name="InclusaBeautyOrchestrator",
            input_summary=f"produto={product.get('name')} perfis={profiles}",
            output_summary=f"{len(checklist)} itens, {len(recs)} recomendações, score={total}",
            tokens_used=tokens_in + tokens_out,
            cost=round(cost, 6),
            latency_ms=latency,
        )],
    )
