# 05 — Tutorial de Implantação e Utilização (passo a passo)

Guia prático e completo para **rodar localmente**, **implantar no Google Cloud**
e **utilizar** a Inclua Beauty AI (backend agêntico + frontend acessível).
Reflete exatamente o código do repositório (`backend/`, `frontend/`,
`infra/terraform/`, `scripts/deploy.sh`).

> Convenções: comandos assumem a raiz do repositório como diretório de trabalho.
> Substitua valores entre `<...>`.

---

## Parte A — Execução local (5 minutos, sem GCP)

Ideal para avaliar a plataforma. Roda com **motor heurístico** (sem custo/IA
externa) e banco **SQLite**.

### A.1 Pré-requisitos

- Python 3.11+ e Node.js 20+ (o projeto foi validado com Python 3.11 e Node 22).

### A.2 Subir o backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

No startup o app:
1. roda as **migrations** (`alembic upgrade head`);
2. carrega a **base normativa** vetorizada (RAG);
3. cria a **conta de demonstração**.

Verifique:
- API: <http://127.0.0.1:8000>
- Swagger/OpenAPI: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health> → `{"status":"ok","engine":"heuristic"}`

Credenciais demo: **`demo@incluabeauty.ai` / `demo1234`**.

### A.3 Subir o frontend (outro terminal)

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

O Vite faz proxy de `/api` para `http://127.0.0.1:8000`. Abra
<http://localhost:5173>, faça login com a conta demo e siga a **Parte C** (uso).

### A.4 Alternativa: tudo via Makefile

```bash
make install        # cria venv do backend + instala frontend
make dev-backend    # sobe a API
make dev-frontend   # (outro terminal) sobe o frontend
make test           # roda os testes
```

---

## Parte B — Implantação no Google Cloud

Leva a plataforma a produção: **Cloud Run** (API + agentes), **Cloud SQL
(PostgreSQL + pgvector)**, **Vertex AI/Gemini**, **Pub/Sub**, **Cloud Storage**,
**Secret Manager** e **IAM** — tudo provisionado por Terraform.

### B.1 Pré-requisitos

| Item | Detalhe |
|---|---|
| Conta GCP | com **Billing** ativo |
| CLIs | `gcloud`, `terraform >= 1.6` |
| Permissão | Owner/Editor no projeto |
| Docker | usado pelo Cloud Build (build remoto; não precisa local) |

```bash
gcloud auth login
gcloud auth application-default login
```

### B.2 Deploy de um comando

```bash
export PROJECT_ID="<seu-projeto>"
export REGION="southamerica-east1"
export VERTEX_LOCATION="us-central1"          # valide a região do Gemini
export TF_VAR_db_password="<senha-forte>"
export TF_VAR_jwt_secret="<32+ caracteres aleatórios>"

make deploy        # equivale a ./scripts/deploy.sh
```

O `scripts/deploy.sh` executa 4 fases:

1. **Infra base** — `terraform apply` de APIs + Artifact Registry.
2. **Imagens** — `gcloud builds submit` builda e publica `api` e `agents`.
3. **Stack completo** — `terraform apply` com as imagens reais (Cloud Run, Cloud
   SQL, Pub/Sub, Storage, Secret Manager, IAM, rede privada).
4. **Pós-deploy** — instrui o `CREATE EXTENSION vector` e faz health check.

Ao final o script imprime a **URL da API** (e `.../docs`).

### B.3 Passo obrigatório pós-deploy: habilitar pgvector

Conecte no banco (Cloud SQL Studio no console, ou Auth Proxy) e rode uma vez:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> Sem isso, o RAG normativo cai no fallback local (funciona, porém sem busca
> vetorial nativa do Postgres).

### B.4 Ativar o raciocínio com Gemini (ADK)

O Terraform já configura os serviços com `ANALYSIS_ENGINE=adk`,
`GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT` e
`GOOGLE_CLOUD_LOCATION`. A SA `sa-agents` recebe `roles/aiplatform.user`. Basta
que o modelo Gemini esteja disponível na `VERTEX_LOCATION`. Se algo falhar em
runtime, o `runner` faz **fallback automático** para o heurístico.

### B.5 Deploy manual (passo a passo, sem o script)

Se preferir controlar cada etapa (equivalente ao `deploy.sh`):

```bash
cd infra/terraform
terraform init
# Fase 1 — cria Artifact Registry e habilita APIs
terraform apply -target=google_project_service.enabled \
                -target=google_artifact_registry_repository.images

# Fase 2 — build/push das imagens
AR="${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images"
gcloud builds submit ../../backend --tag "${AR}/api:v1"
gcloud builds submit ../../backend --tag "${AR}/agents:v1"

# Fase 3 — stack completo com as imagens
terraform apply -var "api_image=${AR}/api:v1" -var "agents_image=${AR}/agents:v1"
```

### B.6 CI/CD (deploys subsequentes)

- **`.github/workflows/ci.yml`**: em cada push/PR roda lint + testes (backend) e
  typecheck + build (frontend).
- **`cloudbuild.yaml`**: pipeline de deploy (testes → build/push → `gcloud run
  deploy`). Dispare com:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=${REGION}
```

### B.7 Migrations em produção (multi-instância)

Por padrão o app roda `alembic upgrade head` no startup. Com várias instâncias,
desligue isso e rode as migrations como passo dedicado:

```bash
# variável de ambiente do serviço:
RUN_MIGRATIONS_ON_START=false
# e no CI/CD, antes do deploy:
alembic upgrade head
```

### B.8 Destruir o ambiente

```bash
make tf-destroy        # terraform destroy (atenção: Cloud SQL tem deletion_protection)
```

---

## Parte C — Utilização da plataforma

Fluxo funcional completo, tanto pela **interface** quanto pela **API**.

### C.1 Papéis e permissões (RBAC)

| Papel | Pode |
|---|---|
| `administrador` | tudo, inclusive criar usuários e ver custos |
| `gestor_marca` | projetos, produtos, análises, relatórios |
| `designer` | produtos, análises, relatórios |
| `especialista` | análises, validar, relatórios, editar normas |
| `regulatorio` | ler análises, relatórios, editar normas |
| `testador_pcd` | ler análises, ler normas |
| `cliente_leitor` | ler análises, ler normas |

O admin cria usuários com papel:

```bash
curl -X POST $API/users -H "$H" -H "Content-Type: application/json" \
  -d '{"name":"Designer X","email":"x@marca.com","password":"secret123","role":"designer"}'
```

### C.2 Jornada pela interface (frontend)

1. **Login** com a conta demo (ou a criada).
2. **Nova análise de embalagem** — preencha:
   - nome do produto, categoria, tipo de tampa;
   - marque os **componentes** (frasco, tampa, rótulo, válvula…);
   - marque os **perfis de necessidade** (baixa visão, artrite, cegueira…);
   - (opcional) **envie a imagem** da embalagem — se o backend estiver em modo
     Gemini, a ingestão multimodal enriquece categoria/tampa/componentes.
3. Clique em **Executar análise**. Em modo assíncrono a UI aguarda a conclusão.
4. **Resultados**:
   - **Score 0–100** por dimensão + **gate** (vermelho/amarelo/verde/azul);
   - **Recomendações** priorizadas com opções mínima/intermediária/premium,
     norma relacionada (com status) e **evidência RAG**;
   - **Checklist** com status por item.
5. **Dashboard de uso e custo de IA** (tokens, custo/análise, por agente).

### C.3 Jornada pela API (curl)

```bash
API=http://127.0.0.1:8000/api/v1      # ou a URL do Cloud Run

# 1) Login
TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d '{"email":"demo@incluabeauty.ai","password":"demo1234"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
H="Authorization: Bearer $TOKEN"

# 2) Projeto
PROJ=$(curl -s -X POST $API/projects -H "$H" -H "Content-Type: application/json" \
  -d '{"name":"Linha Perfumes 2026"}' | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 3) Produto (+ componentes)
PROD=$(curl -s -X POST $API/products -H "$H" -H "Content-Type: application/json" \
  -d "{\"project_id\":\"$PROJ\",\"name\":\"Perfume Aurora\",\"category\":\"perfumes\",\"cap_type\":\"rosca\",\"components\":[{\"component_type\":\"tampa\"},{\"component_type\":\"rotulo\"},{\"component_type\":\"frasco\"}]}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 4) (opcional) Upload de imagem
curl -s -X POST "$API/products/$PROD/images?image_type=embalagem" -H "$H" \
  -F "file=@/caminho/para/foto.jpg"

# 5) Executar análise
RUN=$(curl -s -X POST $API/analysis-runs -H "$H" -H "Content-Type: application/json" \
  -d "{\"product_id\":\"$PROD\",\"profiles\":[\"baixa_visao\",\"artrite\",\"cegueira\"]}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")

# 6) Resultados
curl -s $API/analysis-runs/$RUN/score           -H "$H"
curl -s $API/analysis-runs/$RUN/recommendations -H "$H"
curl -s $API/analysis-runs/$RUN/checklist       -H "$H"
curl -s $API/analysis-runs/$RUN/trace           -H "$H"   # tokens/custo/latência

# 7) Relatório
REP=$(curl -s -X POST $API/reports -H "$H" -H "Content-Type: application/json" \
  -d "{\"analysis_run_id\":\"$RUN\",\"format\":\"json\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s $API/reports/$REP/download -H "$H" -o relatorio.json

# 8) Busca semântica na base normativa (RAG)
curl -s "$API/standards/search?q=tampa+dificil+de+abrir" -H "$H"

# 9) Dashboard de custo (admin)
curl -s $API/admin/usage -H "$H"
```

### C.4 Referência de endpoints

| Método | Rota | Permissão |
|---|---|---|
| POST | `/auth/signup` · `/auth/login` | pública |
| GET | `/me` | autenticado |
| POST | `/users` | admin |
| POST/GET | `/projects` | `project:write` / leitura |
| POST | `/products` · GET `/products/{id}` | `product:write` / leitura |
| POST/GET | `/products/{id}/images` | `product:write` / leitura |
| POST | `/analysis-runs` | `analysis:run` |
| GET | `/analysis-runs/{id}` · `/score` · `/checklist` · `/recommendations` · `/trace` | leitura |
| GET | `/standards` · `/standards/search` | leitura |
| POST | `/reports` · GET `/reports/{id}/download` | `report:write` / leitura |
| GET | `/admin/usage` | admin |

---

## Parte D — Configuração por variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | sqlite local | conexão do banco (Postgres em prod) |
| `RUN_MIGRATIONS_ON_START` | `true` | roda alembic no startup |
| `ANALYSIS_ENGINE` | `heuristic` | `heuristic` \| `adk` (Gemini) |
| `ANALYSIS_MODE` | `sync` | `sync` \| `async` (fila) |
| `QUEUE_BACKEND` | `local` | `local` (thread) \| `pubsub` |
| `GCS_BUCKET` | vazio | bucket de imagens/relatórios (senão, local) |
| `GOOGLE_GENAI_USE_VERTEXAI` | `FALSE` | `TRUE` para Vertex AI |
| `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` | — | projeto/região Vertex |
| `GOOGLE_API_KEY` | vazio | alternativa à Vertex (dev) |
| `JWT_SECRET` | inseguro | **defina em produção** |
| `SEED_DEMO` | `true` | cria conta demo no startup |

---

## Parte E — Solução de problemas

| Sintoma | Causa provável | Ação |
|---|---|---|
| `401 Token inválido` | token expirado/ausente | refaça o login |
| `403 Papel '...' não tem permissão` | RBAC | use um papel com a permissão (ver C.1) |
| Análise sempre `engine: heuristic` mesmo com ADK | credenciais/modelo indisponível | verifique `ANALYSIS_ENGINE=adk`, região do Gemini e IAM `aiplatform.user`; veja logs |
| RAG sem resultados | base não carregada / pgvector ausente | confirme startup (seed) e `CREATE EXTENSION vector` |
| Análise fica em `queued` | modo async sem worker | em local usa thread automática; em GCP confirme a subscription push do Pub/Sub |
| Cloud Run 500 no 1º acesso | cold start / migration | aguarde alguns segundos; veja Cloud Logging |
| `terraform apply` falha em Cloud SQL | peering/rede ainda propagando | rode `apply` novamente |

Logs em produção:

```bash
gcloud logging read \
  'resource.type=cloud_run_revision AND jsonPayload.analysis_run_id="<ID>"' --limit=50
```

---

## Resumo dos comandos essenciais

```bash
# Local
make install && make dev-backend        # + make dev-frontend em outro terminal

# Deploy GCP
export PROJECT_ID=... TF_VAR_db_password=... TF_VAR_jwt_secret=...
make deploy

# Migrations
make migrate
```

Documentos relacionados: [01 — Arquitetura](01-arquitetura-gcp-adk.md) ·
[02 — Instalação detalhada](02-instalacao-gcp.md) · READMEs em `backend/` e
`frontend/` · `infra/terraform/README.md`.
