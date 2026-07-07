"""Seleção do motor de análise e execução com fallback seguro."""
from __future__ import annotations

import logging

from app.agents import adk_engine, heuristic
from app.agents.schemas import AnalysisResult
from app.core.config import settings

log = logging.getLogger("inclua.agents")


def run_analysis(product: dict, profiles: list[str]) -> AnalysisResult:
    """Executa a análise. Usa ADK/Gemini se configurado; senão heurístico.

    Se o motor ADK falhar em runtime, faz fallback automático para o heurístico
    para nunca deixar o usuário sem resultado (resiliência do MVP).
    """
    if settings.analysis_engine == "adk" and adk_engine.available():
        try:
            return adk_engine.analyze(product, profiles)
        except Exception as exc:  # pragma: no cover - depende de credenciais externas
            log.warning("Motor ADK falhou (%s); fallback para heurístico.", exc)
    return heuristic.analyze(product, profiles)
