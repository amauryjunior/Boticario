"""Base normativa e busca vetorial (RF-015/016)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents import rag
from app.api.deps import require_perm
from app.core.roles import P_STANDARDS_READ
from app.db.session import get_db
from app.models import StandardReference, User

router = APIRouter(tags=["standards"])


@router.get("/standards")
def list_standards(
    user: User = Depends(require_perm(P_STANDARDS_READ)), db: Session = Depends(get_db)
):
    return [
        {"id": s.id, "title": s.title, "source": s.source,
         "jurisdiction": s.jurisdiction, "status": s.status}
        for s in db.query(StandardReference).all()
    ]


@router.get("/standards/search")
def search_standards(
    q: str,
    jurisdiction: str | None = None,
    k: int = 4,
    user: User = Depends(require_perm(P_STANDARDS_READ)),
    db: Session = Depends(get_db),
):
    """Busca semântica (RAG) nos trechos normativos."""
    return {"query": q, "matches": rag.search(db, q, jurisdiction=jurisdiction, k=k)}
