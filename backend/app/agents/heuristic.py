"""Motor de análise heurístico determinístico (offline, sem LLM).

Garante que a plataforma rode em qualquer ambiente e serve de baseline/guardrail
para o motor ADK. Aplica as regras da base de conhecimento sobre os componentes
declarados do produto e os perfis de necessidade selecionados.
"""
from __future__ import annotations

import time

from app.agents import knowledge as kb
from app.agents.schemas import (
    AnalysisResult,
    ChecklistFinding,
    RecommendationFinding,
    TraceRecord,
)
from app.agents.scoring import approval_gate, compute_scores, maturity_level


def _component_present(product: dict, component: str) -> bool:
    types = {c.get("component_type", "").lower() for c in product.get("components", [])}
    # frasco/rótulo/tampa costumam existir mesmo se não declarados explicitamente
    if component in {"frasco", "rotulo", "tampa"} and not types:
        return True
    return any(component in t or t in component for t in types)


def analyze(product: dict, profiles: list[str]) -> AnalysisResult:
    t0 = time.perf_counter()
    profile_set = set(profiles)
    checklist: list[ChecklistFinding] = []
    recs: list[RecommendationFinding] = []

    for rule in kb.RULES:
        # A regra só se aplica se algum perfil selecionado for impactado.
        impacted = profile_set.intersection(rule["profiles"])
        if not impacted:
            continue
        if not _component_present(product, rule["component"]):
            continue

        # Regra específica de tampa: só marca barreira se o tipo de tampa é de risco.
        if "trigger_caps" in rule:
            cap = (product.get("cap_type") or "").lower() or None
            if cap not in rule["trigger_caps"]:
                continue

        std = kb.STANDARDS[rule["standard"]]
        impacted_names = ", ".join(kb.PROFILES[p] for p in impacted)
        status = "nao_atende"
        priority = "alta" if profile_set & {"cegueira", "motora", "artrite"} else "media"

        checklist.append(ChecklistFinding(
            dimension=rule["dimension"],
            item=rule["barrier"],
            status=status,
            evidence=f"Impacta: {impacted_names}. {rule['impact']}.",
            priority=priority,
        ))
        recs.append(RecommendationFinding(
            component=rule["component"],
            barrier=rule["barrier"],
            impact=rule["impact"],
            option_min=rule["option_min"],
            option_mid=rule["option_mid"],
            option_premium=rule["option_premium"],
            effort="baixo" if rule["option_min"] else "medio",
            priority=priority,
            evidence_level="a_validar",
            standard_ref=std["ref"],
            standard_status=std["status"],
        ))

    # Itens de baseline (cobertura de checklist RF-012)
    for dim, item, status, ev in kb.BASELINE_CHECKLIST:
        checklist.append(ChecklistFinding(
            dimension=dim, item=item, status=status, evidence=ev, priority="media"
        ))

    # Marca como "atende" as dimensões sem barreira detectada, para o score refletir cobertura.
    covered = {c.dimension for c in checklist}
    for dim in ["Operabilidade e abertura", "Identificação tátil e multisensorial",
                "Leitura, contraste e rotulagem", "Clareza das instruções",
                "Segurança e risco de uso incorreto", "Sustentabilidade e refil"]:
        if dim not in covered:
            checklist.append(ChecklistFinding(
                dimension=dim, item=f"Sem barreira crítica detectada em: {dim}",
                status="atende", evidence="Nenhuma barreira mapeada pelos perfis selecionados.",
                priority="baixa",
            ))

    dims, total = compute_scores(checklist)
    latency = int((time.perf_counter() - t0) * 1000)

    return AnalysisResult(
        engine="heuristic",
        model_used=None,
        checklist=checklist,
        recommendations=recs,
        dimensions=dims,
        score_total=total,
        maturity_level=maturity_level(total),
        gate=approval_gate(total, checklist),
        traces=[TraceRecord(
            agent_name="HeuristicAnalyzer",
            input_summary=f"produto={product.get('name')} perfis={profiles}",
            output_summary=f"{len(checklist)} itens, {len(recs)} recomendações, score={total}",
            latency_ms=latency,
        )],
    )
