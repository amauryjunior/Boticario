# Inclua Beauty AI — Backend (MVP)

Plataforma agêntica em Python (FastAPI) que analisa a **acessibilidade de
embalagens de beleza** e gera checklist, **score 0–100**, recomendações e
relatório. Roda **offline** com um motor heurístico determinístico e, quando
configurado, usa **Google ADK + Gemini/Vertex AI** para o raciocínio dos agentes.

> Documentação de arquitetura, instalação no GCP, mercado e precificação em
> [`../docs/inclua-beauty/`](../docs/inclua-beauty/).

## Requisitos

- Python 3.11+ (imagem de produção usa 3.12)

## Rodar localmente (offline, sem credenciais)

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # opcional; defaults já funcionam
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Docs (OpenAPI/Swagger): http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

No startup, um **seed de demonstração** cria org + usuário + produto exemplo:
- e-mail: `demo@incluabeauty.ai` · senha: `demo1234`

## Testes

```bash
pytest
```

## Fluxo de uso (exemplo)

```bash
API=http://127.0.0.1:8000/api/v1

# login
TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d '{"email":"demo@incluabeauty.ai","password":"demo1234"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
H="Authorization: Bearer $TOKEN"

# criar projeto e produto
PROJ=$(curl -s -X POST $API/projects -H "$H" -H "Content-Type: application/json" \
  -d '{"name":"Linha 2026"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
PROD=$(curl -s -X POST $API/products -H "$H" -H "Content-Type: application/json" \
  -d "{\"project_id\":\"$PROJ\",\"name\":\"Perfume Aurora\",\"category\":\"perfumes\",\"cap_type\":\"rosca\",\"components\":[{\"component_type\":\"tampa\"},{\"component_type\":\"rotulo\"}]}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# análise + score + recomendações + relatório
RUN=$(curl -s -X POST $API/analysis-runs -H "$H" -H "Content-Type: application/json" \
  -d "{\"product_id\":\"$PROD\",\"profiles\":[\"baixa_visao\",\"artrite\"]}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s $API/analysis-runs/$RUN/score           -H "$H"
curl -s $API/analysis-runs/$RUN/recommendations -H "$H"
curl -s -X POST $API/reports -H "$H" -H "Content-Type: application/json" \
  -d "{\"analysis_run_id\":\"$RUN\",\"format\":\"json\"}"
```

## Ativar a camada agêntica (Google ADK + Gemini)

```bash
pip install -e ".[adk]"
# Vertex AI (produção GCP):
export ANALYSIS_ENGINE=adk
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=<seu-projeto>
export GOOGLE_CLOUD_LOCATION=us-central1
# ou Gemini API key (dev):  export GOOGLE_API_KEY=...
```

Se o ADK/credenciais não estiverem disponíveis em runtime, o serviço faz
**fallback automático** para o motor heurístico (nunca deixa o usuário sem
resultado).

## Arquitetura do código

```
backend/app/
├── main.py                 # app FastAPI + lifespan (cria tabelas, seed)
├── core/                   # config (env) e segurança (JWT, hash PBKDF2)
├── db/                     # engine/sessão SQLAlchemy + seed demo
├── models/                 # ORM (Organization, Project, Product, AnalysisRun, ...)
├── schemas/                # contratos Pydantic da API
├── agents/                 # inteligência
│   ├── knowledge.py        # base de conhecimento (barreiras, tampas, normas)
│   ├── scoring.py          # Índice Inclua Beauty (pesos RF-020) + gates
│   ├── heuristic.py        # motor determinístico (offline)
│   ├── adk_engine.py       # malha de agentes Google ADK + Gemini
│   ├── schemas.py          # structured outputs auditáveis
│   └── runner.py           # seleção de motor + fallback
├── services/               # orquestração + persistência da análise
└── api/routers/            # auth, projects, analysis, reports
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/signup` · `/auth/login` | cadastro / login (JWT) |
| GET  | `/api/v1/me` | usuário atual |
| POST/GET | `/api/v1/projects` | projetos |
| POST | `/api/v1/products` · GET `/products/{id}` | produtos + componentes |
| POST/GET | `/api/v1/products/{id}/images` | upload/listagem de imagens (ingestão multimodal) |
| POST | `/api/v1/analysis-runs` | executa a análise (sync ou async) |
| GET | `/api/v1/analysis-runs/{id}/score` · `/checklist` · `/recommendations` · `/trace` | resultados e traces |
| GET | `/api/v1/standards` · `/standards/search?q=` | base normativa + busca vetorial (RAG) |
| GET | `/api/v1/admin/usage` | dashboard de uso e custo de IA (RNF-012) |
| POST | `/api/v1/reports` · GET `/reports/{id}/download` | relatório |

### Modos de execução (variáveis de ambiente)

- `ANALYSIS_MODE=sync|async` — síncrono (default) ou fila.
- `QUEUE_BACKEND=local|pubsub` — thread local (default) ou Google Pub/Sub.
- `UPLOADS_DIR` / `GCS_BUCKET` — armazenamento local ou Google Cloud Storage.

Em produção (GCP), o endpoint interno `POST /api/v1/internal/pubsub/analysis`
recebe o push do Pub/Sub e processa a análise no serviço de agentes.

## Notas de produção

- **Banco**: trocar `DATABASE_URL` para Cloud SQL (PostgreSQL + pgvector).
- **Assíncrono**: no MVP a análise é síncrona; em produção publicar em Pub/Sub e
  processar no serviço de agentes (ver `docs/inclua-beauty/02-instalacao-gcp.md`).
- **Segurança**: definir `JWT_SECRET` forte; segredos no Secret Manager.
- **Deploy**: `Dockerfile` pronto para Cloud Run (usa `$PORT`).
