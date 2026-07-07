"""Índice Inclua Beauty de Acessibilidade do Produto (RF-020/RF-021)."""
from __future__ import annotations

from app.agents.schemas import ChecklistFinding, DimensionScore

# Pesos por dimensão (somam 100) — conforme RF-020.
DIMENSION_WEIGHTS: dict[str, int] = {
    "Operabilidade e abertura": 20,
    "Identificação tátil e multisensorial": 20,
    "Leitura, contraste e rotulagem": 15,
    "Clareza das instruções": 10,
    "Segurança e risco de uso incorreto": 15,
    "Sustentabilidade e refil": 10,
    "Inovação inclusiva": 5,
    "Evidência/teste com usuário": 5,
}

# Contribuição de cada status para o score da dimensão (0..1).
_STATUS_SCORE = {
    "atende": 1.0,
    "parcial": 0.5,
    "a_validar": 0.4,
    "nao_atende": 0.0,
    "nao_aplicavel": None,  # não conta
}


def score_dimension(findings: list[ChecklistFinding]) -> float:
    vals = [_STATUS_SCORE[f.status] for f in findings if _STATUS_SCORE.get(f.status) is not None]
    if not vals:
        return 0.0
    return round(100 * sum(vals) / len(vals), 1)


def compute_scores(checklist: list[ChecklistFinding]) -> tuple[list[DimensionScore], float]:
    by_dim: dict[str, list[ChecklistFinding]] = {d: [] for d in DIMENSION_WEIGHTS}
    for f in checklist:
        by_dim.setdefault(f.dimension, []).append(f)

    dims: list[DimensionScore] = []
    weighted_sum = 0.0
    total_weight = 0
    for dim, weight in DIMENSION_WEIGHTS.items():
        s = score_dimension(by_dim.get(dim, []))
        dims.append(DimensionScore(dimension=dim, weight=weight, score=s))
        weighted_sum += s * weight
        total_weight += weight

    total = round(weighted_sum / total_weight, 1) if total_weight else 0.0
    return dims, total


def maturity_level(total: float) -> str:
    if total >= 90:
        return "Referência inclusiva"
    if total >= 75:
        return "Avançado"
    if total >= 60:
        return "Intermediário"
    if total >= 40:
        return "Básico"
    return "Crítico"


def approval_gate(total: float, checklist: list[ChecklistFinding]) -> str:
    has_blocking = any(
        f.status == "nao_atende" and f.priority == "alta" for f in checklist
    )
    if has_blocking or total < 40:
        return "vermelho"
    if total < 75:
        return "amarelo"
    if total >= 90:
        return "azul"
    return "verde"
