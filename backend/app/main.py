"""Inclua Beauty AI — aplicação FastAPI (ponto de entrada)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import analysis, auth, projects, reports
from app.core.config import settings
from app.db.seed import seed_demo
from app.db.session import Base, SessionLocal, engine

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo:
        with SessionLocal() as db:
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


for r in (auth.router, projects.router, analysis.router, reports.router):
    app.include_router(r, prefix=settings.api_v1_prefix)
