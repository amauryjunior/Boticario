"""Administração: uso e custo de IA por organização (RNF-012)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_perm
from app.core.roles import P_ADMIN
from app.db.session import get_db
from app.models import (
    AgentTrace,
    AnalysisRun,
    Product,
    Project,
    User,
)
from app.schemas.api import UsageOut

router = APIRouter(tags=["admin"])


@router.get("/admin/usage", response_model=UsageOut)
def usage(user: User = Depends(require_perm(P_ADMIN)), db: Session = Depends(get_db)) -> UsageOut:
    """Agrega tokens, custo e latência das análises da organização do usuário."""
    # runs da organização (via project -> product -> run)
    run_ids = [
        r.id for r in (
            db.query(AnalysisRun)
            .join(Product, AnalysisRun.product_id == Product.id)
            .join(Project, Product.project_id == Project.id)
            .filter(Project.organization_id == user.organization_id)
            .all()
        )
    ]
    total_analyses = len(run_ids)
    if not run_ids:
        return UsageOut(total_analyses=0, total_tokens=0, total_cost_usd=0.0,
                        avg_cost_per_analysis_usd=0.0, avg_latency_ms=0.0, by_agent=[])

    traces = db.query(AgentTrace).filter(AgentTrace.analysis_run_id.in_(run_ids)).all()
    total_tokens = sum(t.tokens_used for t in traces)
    total_cost = sum(t.cost for t in traces)
    avg_latency = (sum(t.latency_ms for t in traces) / len(traces)) if traces else 0.0

    by_agent_rows = (
        db.query(
            AgentTrace.agent_name,
            func.count(AgentTrace.id),
            func.sum(AgentTrace.tokens_used),
            func.sum(AgentTrace.cost),
        )
        .filter(AgentTrace.analysis_run_id.in_(run_ids))
        .group_by(AgentTrace.agent_name)
        .all()
    )
    by_agent = [
        {"agent": name, "calls": calls, "tokens": int(tokens or 0),
         "cost_usd": round(float(cost or 0.0), 6)}
        for name, calls, tokens, cost in by_agent_rows
    ]

    return UsageOut(
        total_analyses=total_analyses,
        total_tokens=int(total_tokens),
        total_cost_usd=round(float(total_cost), 6),
        avg_cost_per_analysis_usd=round(float(total_cost) / total_analyses, 6),
        avg_latency_ms=round(avg_latency, 1),
        by_agent=by_agent,
    )
