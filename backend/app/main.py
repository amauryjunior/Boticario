"""Inclua Beauty AI — aplicação FastAPI (ponto de entrada)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agents import rag
from app.api.routers import admin, analysis, auth, projects, reports, standards
from app.core.config import settings
from app.db.migrate import upgrade_head
from app.db.seed import seed_demo
from app.db.session import Base, SessionLocal, engine

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.run_migrations_on_start:
        upgrade_head()
    else:
        # Ambiente onde as migrations rodam como passo separado de CI/CD.
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        rag.seed_chunks(db)  # base normativa vetorizada (RAG)
        if settings.seed_demo:
            seed_demo(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    summary="Plataforma agêntica para acessibilidade de embalagens de beleza",
    lifespan=lifespan,
)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "engine": settings.analysis_engine}


for r in (auth.router, projects.router, analysis.router, reports.router,
          standards.router, admin.router):
    app.include_router(r, prefix=settings.api_v1_prefix)
