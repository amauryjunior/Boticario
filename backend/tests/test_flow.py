"""Teste end-to-end do fluxo principal (RF-004 → relatório)."""
from __future__ import annotations

import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SEED_DEMO"] = "false"
os.environ["ANALYSIS_ENGINE"] = "heuristic"

from fastapi.testclient import TestClient  # noqa: E402

from app.agents import rag  # noqa: E402
from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    rag.seed_chunks(_db)  # base normativa vetorizada p/ RAG nos testes
client = TestClient(app)
API = "/api/v1"


def _auth_as(email: str) -> dict:
    r = client.post(f"{API}/auth/signup", json={
        "organization_name": "Test Beauty", "name": "Tester",
        "email": email, "password": "secret123",
    })
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _auth() -> dict:
    return _auth_as("tester@example.com")


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


def test_rag_traces_and_usage():
    headers = _auth_as("rag@example.com")
    proj = client.post(f"{API}/projects", headers=headers, json={"name": "P"}).json()
    prod = client.post(f"{API}/products", headers=headers, json={
        "project_id": proj["id"], "name": "Batom", "category": "maquiagem",
        "cap_type": "rosca", "components": [{"component_type": "tampa"},
                                            {"component_type": "rotulo"}],
    }).json()
    run = client.post(f"{API}/analysis-runs", headers=headers, json={
        "product_id": prod["id"], "profiles": ["baixa_visao", "artrite"],
    }).json()

    # RAG: recomendações trazem evidência normativa recuperada
    recs = client.get(f"{API}/analysis-runs/{run['id']}/recommendations", headers=headers).json()
    assert any(r["norm_evidence"] for r in recs)

    # busca semântica na base normativa
    search = client.get(f"{API}/standards/search", headers=headers,
                        params={"q": "tampa difícil de abrir força"}).json()
    assert len(search["matches"]) > 0

    # traces por agente
    trace = client.get(f"{API}/analysis-runs/{run['id']}/trace", headers=headers).json()
    assert len(trace) >= 1

    # dashboard de uso/custo
    usage = client.get(f"{API}/admin/usage", headers=headers).json()
    assert usage["total_analyses"] >= 1
    assert "by_agent" in usage


def test_async_mode():
    import time

    from app.core.config import settings
    settings.analysis_mode = "async"
    try:
        headers = _auth_as("async@example.com")
        proj = client.post(f"{API}/projects", headers=headers, json={"name": "P"}).json()
        prod = client.post(f"{API}/products", headers=headers, json={
            "project_id": proj["id"], "name": "Sérum", "category": "skincare",
            "cap_type": "rosca", "components": [{"component_type": "tampa"}],
        }).json()
        run = client.post(f"{API}/analysis-runs", headers=headers, json={
            "product_id": prod["id"], "profiles": ["artrite"],
        }).json()
        assert run["status"] in {"queued", "running", "done"}

        # aguarda o worker (thread local) concluir
        for _ in range(50):
            r = client.get(f"{API}/analysis-runs/{run['id']}", headers=headers).json()
            if r["status"] == "done":
                break
            time.sleep(0.1)
        assert r["status"] == "done"
    finally:
        settings.analysis_mode = "sync"


def test_rbac_enforced():
    admin = _auth_as("admin_rbac@example.com")  # signup => administrador
    # admin cria um testador_pcd (papel só de leitura)
    r = client.post(f"{API}/users", headers=admin, json={
        "name": "Tester PcD", "email": "pcd@example.com",
        "password": "secret123", "role": "testador_pcd",
    })
    assert r.status_code == 201, r.text

    tester = client.post(f"{API}/auth/login", json={
        "email": "pcd@example.com", "password": "secret123",
    }).json()
    th = {"Authorization": f"Bearer {tester['access_token']}"}

    # testador_pcd NÃO pode criar projeto (403)
    forbidden = client.post(f"{API}/projects", headers=th, json={"name": "X"})
    assert forbidden.status_code == 403

    # testador_pcd NÃO pode ver /admin/usage (403)
    assert client.get(f"{API}/admin/usage", headers=th).status_code == 403

    # mas PODE buscar normas (leitura permitida)
    assert client.get(f"{API}/standards/search", headers=th,
                      params={"q": "contraste"}).status_code == 200


def test_scoring_levels():
    from app.agents.scoring import maturity_level
    assert maturity_level(95) == "Referência inclusiva"
    assert maturity_level(30) == "Crítico"
