"""Geração e download de relatórios (RF-026/027)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.agents.schemas import ChecklistFinding
from app.agents.scoring import approval_gate, compute_scores, maturity_level
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import AnalysisRun, ChecklistItem, Product, Recommendation, Report, User
from app.schemas.api import ReportIn, ReportOut

router = APIRouter(tags=["reports"])


def _build_report_content(db: Session, run: AnalysisRun) -> dict:
    product = db.get(Product, run.product_id)
    items = db.query(ChecklistItem).filter(ChecklistItem.analysis_run_id == run.id).all()
    recs = db.query(Recommendation).filter(Recommendation.analysis_run_id == run.id).all()
    findings = [
        ChecklistFinding(dimension=i.dimension, item=i.item, status=i.status,
                         evidence=i.evidence or "", priority=i.priority or "media")
        for i in items
    ]
    dims, total = compute_scores(findings)
    return {
        "produto": {"nome": product.name, "marca": product.brand,
                    "categoria": product.category, "tampa": product.cap_type},
        "score": {"total": total, "nivel": maturity_level(total),
                  "gate": approval_gate(total, findings),
                  "dimensoes": [d.model_dump() for d in dims]},
        "checklist": [
            {"dimensao": i.dimension, "item": i.item, "status": i.status,
             "evidencia": i.evidence, "prioridade": i.priority} for i in items
        ],
        "recomendacoes": [
            {"componente": r.component, "barreira": r.barrier, "impacto": r.impact,
             "minimo": r.option_min, "intermediario": r.option_mid,
             "premium": r.option_premium, "norma": r.standard_ref,
             "status_norma": r.standard_status, "prioridade": r.priority,
             "nivel_evidencia": r.evidence_level} for r in recs
        ],
        "aviso": ("Recomendações geradas por IA/heurística. Não constituem "
                  "conformidade legal definitiva; itens 'a_validar' exigem "
                  "validação por especialista (RNF-015)."),
    }


@router.post("/reports", response_model=ReportOut, status_code=201)
def create_report(
    body: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Report:
    run = db.get(AnalysisRun, body.analysis_run_id)
    if not run:
        raise HTTPException(404, "Análise não encontrada")
    content = json.dumps(_build_report_content(db, run), ensure_ascii=False, indent=2)
    existing = db.query(Report).filter(Report.analysis_run_id == run.id).count()
    report = Report(
        analysis_run_id=run.id, format=body.format, content=content, version=existing + 1
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(404, "Relatório não encontrado")
    return Response(
        content=report.content or "{}",
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.json"'},
    )
