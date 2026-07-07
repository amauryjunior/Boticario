"""Serviço de análise: orquestra o motor de agentes e persiste os resultados."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.runner import run_analysis
from app.models import (
    AgentTrace,
    AnalysisRun,
    ChecklistItem,
    Product,
    Recommendation,
)


def _product_to_dict(product: Product) -> dict:
    return {
        "name": product.name,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "target_user": product.target_user,
        "cap_type": product.cap_type,
        "components": [
            {"component_type": c.component_type, "material": c.material,
             "dimensions": c.dimensions, "description": c.description}
            for c in product.components
        ],
    }


def execute_analysis(db: Session, run: AnalysisRun, product: Product) -> AnalysisRun:
    """Executa a malha de agentes e grava checklist, recomendações e traces."""
    profiles = json.loads(run.profiles) if run.profiles else []
    result = run_analysis(_product_to_dict(product), profiles)

    for f in result.checklist:
        db.add(ChecklistItem(
            analysis_run_id=run.id, dimension=f.dimension, item=f.item,
            status=f.status, evidence=f.evidence, priority=f.priority,
        ))
    for r in result.recommendations:
        db.add(Recommendation(
            analysis_run_id=run.id, component=r.component, barrier=r.barrier,
            impact=r.impact, option_min=r.option_min, option_mid=r.option_mid,
            option_premium=r.option_premium, effort=r.effort, priority=r.priority,
            evidence_level=r.evidence_level, standard_ref=r.standard_ref,
            standard_status=r.standard_status,
        ))
    for t in result.traces:
        db.add(AgentTrace(
            analysis_run_id=run.id, agent_name=t.agent_name,
            input_summary=t.input_summary, output_summary=t.output_summary,
            tokens_used=t.tokens_used, cost=t.cost, latency_ms=t.latency_ms,
        ))

    run.status = "done"
    run.score_total = result.score_total
    run.maturity_level = result.maturity_level
    run.engine = result.engine
    run.model_used = result.model_used
    run.finished_at = datetime.now(timezone.utc)

    # guarda o detalhamento de dimensões e gate para o endpoint de score
    run_score_cache[run.id] = {
        "gate": result.gate,
        "dimensions": [d.model_dump() for d in result.dimensions],
    }

    db.commit()
    db.refresh(run)
    return run


# Cache simples em memória do detalhamento de score por run (MVP).
run_score_cache: dict[str, dict] = {}
