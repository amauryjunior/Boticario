"""Execução programática das migrations Alembic (substitui create_all)."""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.db.session import Base, engine

log = logging.getLogger("inclua.migrate")

_BACKEND_DIR = Path(__file__).resolve().parents[2]  # .../backend


def _alembic_config() -> Config:
    cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    return cfg


def upgrade_head() -> None:
    """Aplica todas as migrations pendentes. Fallback para create_all em erro."""
    try:
        command.upgrade(_alembic_config(), "head")
        log.info("Migrations aplicadas (alembic upgrade head).")
    except Exception as exc:  # pragma: no cover - fallback de segurança
        log.warning("Alembic falhou (%s); usando create_all como fallback.", exc)
        Base.metadata.create_all(bind=engine)
