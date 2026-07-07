"""Teste end-to-end do fluxo principal (RF-004 → relatório)."""
from __future__ import annotations

import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SEED_DEMO"] = "false"
os.environ["ANALYSIS_ENGINE"] = "heuristic"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)
client = TestClient(app)
API = "/api/v1"


def _auth() -> dict:
    r = client.post(f"{API}/auth/signup", json={
        "organization_name": "Test Beauty", "name": "Tester",
        "email": "tester@example.com", "password": "secret123",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_analysis():
    headers = _auth()

    # /me
    assert client.get(f"{API}/me", headers=headers).json()["email"] == "tester@example.com"

    # projeto
    proj = client.post(f"{API}/projects", headers=headers,
                       json={"name": "Linha 2026"}).json()

    # produto com tampa de rosca (dispara barreira de operabilidade)
    prod = client.post(f"{API}/products", headers=headers, json={
        "project_id": proj["id"], "name": "Perfume Teste", "category": "perfumes",
        "cap_type": "rosca",
        "components": [{"component_type": "tampa"}, {"component_type": "rotulo"},
                       {"component_type": "frasco"}],
    }).json()

    # análise para perfis com barreiras
    run = client.post(f"{API}/analysis-runs", headers=headers, json={
        "product_id": prod["id"],
        "profiles": ["baixa_visao", "artrite", "cegueira"],
    }).json()
    assert run["status"] == "done"
    assert run["engine"] == "heuristic"

    # score
    score = client.get(f"{API}/analysis-runs/{run['id']}/score", headers=headers).json()
    assert 0 <= score["score_total"] <= 100
    assert len(score["dimensions"]) == 8
    assert score["gate"] in {"vermelho", "amarelo", "verde", "azul"}

    # checklist e recomendações não vazios
    checklist = client.get(f"{API}/analysis-runs/{run['id']}/checklist", headers=headers).json()
    recs = client.get(f"{API}/analysis-runs/{run['id']}/recommendations", headers=headers).json()
    assert len(checklist) > 0
    assert len(recs) > 0
    # cada recomendação tem 3 alternativas e status de norma (RF-023/RF-016)
    assert all(r["standard_status"] for r in recs)

    # relatório
    rep = client.post(f"{API}/reports", headers=headers,
                      json={"analysis_run_id": run["id"], "format": "json"}).json()
    dl = client.get(f"{API}/reports/{rep['id']}/download", headers=headers)
    assert dl.status_code == 200
    assert "recomendacoes" in dl.text


def test_scoring_levels():
    from app.agents.scoring import maturity_level
    assert maturity_level(95) == "Referência inclusiva"
    assert maturity_level(30) == "Crítico"
