"""Serviço de análise: orquestra o motor de agentes e persiste os resultados."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

import mimetypes

from app.agents import ingestion, rag
from app.agents.runner import run_analysis
from app.models import (
    AgentTrace,
    AnalysisRun,
    ChecklistItem,
    Product,
    Recommendation,
)
from app.services import storage


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


def _enrich_from_images(db: Session, product: Product, pdict: dict) -> None:
    """Ingestão multimodal: enriquece o produto com atributos detectados na imagem."""
    if not product.images or not ingestion.available():
        return
    try:
        img = product.images[0]
        data = storage.read(img.file_url)
        mime = mimetypes.guess_type(img.file_url)[0] or "image/png"
        text = f"{product.name}. {product.description or ''}"
        res = ingestion.ingest(data, mime, text)
    except Exception:
        return
    if not res:
        return
    if res.category and not pdict.get("category"):
        pdict["category"] = res.category
    if res.cap_type and not pdict.get("cap_type"):
        pdict["cap_type"] = res.cap_type
    existing = {c["component_type"] for c in pdict["components"]}
    for comp in res.detected_components:
        if comp not in existing:
            pdict["components"].append({"component_type": comp, "material": None,
                                        "dimensions": None, "description": "detectado por IA"})


def execute_analysis(db: Session, run: AnalysisRun, product: Product) -> AnalysisRun:
    """Executa a malha de agentes e grava checklist, recomendações e traces."""
    profiles = json.loads(run.profiles) if run.profiles else []
    pdict = _product_to_dict(product)
    _enrich_from_images(db, product, pdict)
    result = run_analysis(pdict, profiles)

    for f in result.checklist:
        db.add(ChecklistItem(
            analysis_run_id=run.id, dimension=f.dimension, item=f.item,
            status=f.status, evidence=f.evidence, priority=f.priority,
        ))
    for r in result.recommendations:
        # RAG normativo: recupera o trecho de norma mais relevante para a barreira.
        hits = rag.search(db, r.barrier, jurisdiction=None, k=1)
        norm_evidence = None
        std_ref, std_status = r.standard_ref, r.standard_status
        if hits:
            top = hits[0]
            norm_evidence = f"{top['title']}: {top['chunk']}"
            if not std_ref:
                std_ref, std_status = top["title"], top["status"]
        db.add(Recommendation(
            analysis_run_id=run.id, component=r.component, barrier=r.barrier,
            impact=r.impact, option_min=r.option_min, option_mid=r.option_mid,
            option_premium=r.option_premium, effort=r.effort, priority=r.priority,
            evidence_level=r.evidence_level, standard_ref=std_ref,
            standard_status=std_status, norm_evidence=norm_evidence,
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
