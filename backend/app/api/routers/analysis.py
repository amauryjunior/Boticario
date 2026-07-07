"""Execução e leitura de análises (RF-020 score, checklist, recomendações)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.schemas import ChecklistFinding
from app.agents.scoring import approval_gate, compute_scores, maturity_level
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import AgentTrace, AnalysisRun, ChecklistItem, Product, Recommendation, User
from app.schemas.api import (
    AnalysisRunIn,
    AnalysisRunOut,
    ChecklistItemOut,
    RecommendationOut,
    ScoreDimension,
    ScoreOut,
    TraceOut,
)
from app.services.analysis_service import execute_analysis
from app.services.queue import enqueue_analysis

router = APIRouter(tags=["analysis"])


@router.post("/analysis-runs", response_model=AnalysisRunOut, status_code=201)
def create_analysis_run(
    body: AnalysisRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AnalysisRun:
    product = db.get(Product, body.product_id)
    if not product:
        raise HTTPException(404, "Produto não encontrado")
    run = AnalysisRun(
        product_id=product.id, status="queued", profiles=json.dumps(body.profiles)
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if settings.analysis_mode == "async":
        # Retorna imediatamente; processamento em fila (Pub/Sub) ou thread local.
        enqueue_analysis(run.id)
        return run
    # Execução síncrona (default do MVP).
    run.status = "running"
    db.commit()
    return execute_analysis(db, run, product)


@router.get("/analysis-runs/{run_id}", response_model=AnalysisRunOut)
def get_run(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(404, "Análise não encontrada")
    return run


@router.get("/analysis-runs/{run_id}/trace", response_model=list[TraceOut])
def get_trace(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Traces por agente (RNF-004/005): tokens, custo e latência."""
    return db.query(AgentTrace).filter(AgentTrace.analysis_run_id == run_id).all()


@router.get("/analysis-runs/{run_id}/checklist", response_model=list[ChecklistItemOut])
def get_checklist(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ChecklistItem).filter(ChecklistItem.analysis_run_id == run_id).all()


@router.get("/analysis-runs/{run_id}/recommendations", response_model=list[RecommendationOut])
def get_recommendations(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Recommendation).filter(Recommendation.analysis_run_id == run_id).all()


@router.get("/analysis-runs/{run_id}/score", response_model=ScoreOut)
def get_score(run_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, run_id)
    if not run:
        raise HTTPException(404, "Análise não encontrada")
    items = db.query(ChecklistItem).filter(ChecklistItem.analysis_run_id == run_id).all()
    findings = [
        ChecklistFinding(dimension=i.dimension, item=i.item, status=i.status,
                         evidence=i.evidence or "", priority=i.priority or "media")
        for i in items
    ]
    dims, total = compute_scores(findings)
    return ScoreOut(
        score_total=total,
        maturity_level=maturity_level(total),
        gate=approval_gate(total, findings),
        dimensions=[ScoreDimension(**d.model_dump()) for d in dims],
    )


@router.post("/internal/pubsub/analysis", include_in_schema=False)
async def pubsub_push(payload: dict):
    """Endpoint de push do Pub/Sub (worker de agentes em produção GCP).

    Recebe a mensagem {message: {data: base64(json{run_id})}} e processa.
    Protegido em produção por OIDC do Cloud Run (push-auth-service-account).
    """
    import base64

    from app.services.queue import process_analysis

    try:
        data = payload["message"]["data"]
        run_id = json.loads(base64.b64decode(data).decode())["run_id"]
    except Exception:
        raise HTTPException(400, "Mensagem Pub/Sub inválida")
    process_analysis(run_id)
    return {"status": "processed", "run_id": run_id}
