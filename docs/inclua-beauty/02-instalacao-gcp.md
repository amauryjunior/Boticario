# 02 — Instalação e Utilização no Google Cloud Platform

Guia operacional completo, passo a passo, para provisionar, implantar e operar a
**Inclua Beauty AI** no GCP. Cobre desde o bootstrap do projeto até o uso da
plataforma pelo cliente final. Os comandos assumem `gcloud` CLI instalado e um
usuário com papel de **Owner/Editor** no projeto (ou uma organização GCP).

> Convenções: substitua os valores entre `<...>`. Região padrão sugerida:
> `southamerica-east1` (São Paulo) para latência/soberania de dados no Brasil;
> use `us-central1` se algum recurso/quota de Vertex AI não estiver disponível
> em SP na data de instalação (**valide as regiões suportadas do modelo Gemini
> antes**).

---

## 0. Pré-requisitos

| Item | Detalhe |
|---|---|
| Conta GCP | com **Billing** ativo |
| CLI | `gcloud` (Cloud SDK), `terraform >= 1.6`, `docker`, `psql` |
| Permissões | Owner no projeto, ou `resourcemanager.projectCreator` na org |
| Domínio | opcional, para mapear no Load Balancer (ex.: `app.incluabeauty.ai`) |
| Orçamento | criar Budget + alertas antes de ligar Vertex AI |

```bash
# Autenticação
gcloud auth login
gcloud auth application-default login   # credenciais p/ Terraform/SDK
gcloud components update
```

---

## 1. Bootstrap do projeto e faturamento

```bash
export PROJECT_ID="inclua-beauty-prod"
export REGION="southamerica-east1"
export BILLING_ACCOUNT="<XXXXXX-XXXXXX-XXXXXX>"

# Cria o projeto (ou use um existente)
gcloud projects create "$PROJECT_ID" --name="Inclua Beauty AI - Prod"

# Vincula o faturamento
gcloud billing projects link "$PROJECT_ID" \
  --billing-account="$BILLING_ACCOUNT"

gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"
```

### 1.1 Orçamento e alertas (faça ANTES de habilitar IA)

```bash
gcloud billing budgets create \
  --billing-account="$BILLING_ACCOUNT" \
  --display-name="Inclua Beauty Prod Budget" \
  --budget-amount=2000BRL \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.9 \
  --threshold-rule=percent=1.0
```

---

## 2. Habilitar APIs necessárias

```bash
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudkms.googleapis.com \
  identitytoolkit.googleapis.com \
  vpcaccess.googleapis.com \
  compute.googleapis.com \
  cloudtrace.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

---

## 3. Identidades de serviço (least privilege)

```bash
# SA da API
gcloud iam service-accounts create sa-api \
  --display-name="Inclua Beauty API"

# SA dos agentes (acesso a Vertex AI)
gcloud iam service-accounts create sa-agents \
  --display-name="Inclua Beauty Agents"

export SA_API="sa-api@${PROJECT_ID}.iam.gserviceaccount.com"
export SA_AGENTS="sa-agents@${PROJECT_ID}.iam.gserviceaccount.com"

# Papéis mínimos para os agentes
for ROLE in \
  roles/aiplatform.user \
  roles/cloudsql.client \
  roles/storage.objectAdmin \
  roles/pubsub.subscriber \
  roles/secretmanager.secretAccessor \
  roles/cloudtrace.agent \
  roles/logging.logWriter ; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_AGENTS}" --role="$ROLE"
done

# Papéis mínimos para a API
for ROLE in \
  roles/cloudsql.client \
  roles/storage.objectAdmin \
  roles/pubsub.publisher \
  roles/secretmanager.secretAccessor \
  roles/logging.logWriter ; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_API}" --role="$ROLE"
done
```

---

## 4. Rede privada (VPC + conector Serverless)

```bash
gcloud compute networks create ib-vpc --subnet-mode=custom
gcloud compute networks subnets create ib-subnet \
  --network=ib-vpc --region="$REGION" --range=10.10.0.0/24

# Conector para Cloud Run acessar Cloud SQL via IP privado
gcloud compute networks vpc-access connectors create ib-connector \
  --region="$REGION" --network=ib-vpc --range=10.8.0.0/28
```

---

## 5. Banco de dados: Cloud SQL (PostgreSQL + pgvector)

```bash
gcloud sql instances create ib-postgres \
  --database-version=POSTGRES_16 \
  --region="$REGION" \
  --tier=db-custom-2-7680 \
  --storage-auto-increase \
  --availability-type=REGIONAL \
  --no-assign-ip \
  --network=projects/${PROJECT_ID}/global/networks/ib-vpc

gcloud sql databases create incluabeauty --instance=ib-postgres
gcloud sql users create ib_app --instance=ib-postgres --password="<STRONG_PWD>"
```

Habilitar a extensão `pgvector` (via Cloud SQL Auth Proxy ou console):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
-- Tabela de chunks normativos (RAG)
CREATE TABLE standard_chunks (
  id BIGSERIAL PRIMARY KEY,
  title TEXT, source TEXT, jurisdiction TEXT,
  status TEXT,                    -- confirmada | hipótese | referência ...
  chunk TEXT,
  embedding vector(768)          -- text-embedding-004
);
CREATE INDEX ON standard_chunks USING hnsw (embedding vector_cosine_ops);
```

> As migrations de schema (tabelas do doc de requisitos) são versionadas com
> **Alembic** e aplicadas pelo Cloud Build no deploy.

---

## 6. Armazenamento, filas e segredos

```bash
# Buckets (imagens de produto e relatórios)
gcloud storage buckets create gs://${PROJECT_ID}-uploads \
  --location="$REGION" --uniform-bucket-level-access
gcloud storage buckets create gs://${PROJECT_ID}-reports \
  --location="$REGION" --uniform-bucket-level-access

# Pub/Sub (análise assíncrona + revisão humana)
gcloud pubsub topics create analysis-requested
gcloud pubsub topics create review-requested
gcloud pubsub subscriptions create analysis-worker \
  --topic=analysis-requested --ack-deadline=120

# Segredos
printf '<DB_URL>'   | gcloud secrets create db-url --data-file=-
printf '<JWT_KEY>'  | gcloud secrets create jwt-signing-key --data-file=-
```

---

## 7. Vertex AI (Gemini) — verificação de acesso

```bash
# Confirma que a região oferece o modelo desejado antes do deploy
gcloud ai models list --region="$REGION" 2>/dev/null | head

# Teste rápido de inferência
cat > /tmp/req.json <<'EOF'
{ "contents": [{ "role": "user", "parts": [{ "text": "Responda: OK" }] }] }
EOF
curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/publishers/google/models/gemini-2.5-flash:generateContent" \
  -d @/tmp/req.json
```

> Se o modelo não estiver disponível em `southamerica-east1`, aponte
> `VERTEX_LOCATION` dos agentes para `us-central1` (mantendo dados de negócio no
> Cloud SQL de SP). Ative **Provisioned Throughput** apenas quando o volume
> justificar previsibilidade de custo/latência.

---

## 8. Build e deploy (Cloud Run)

### 8.1 Artifact Registry + imagens

```bash
gcloud artifacts repositories create ib-images \
  --repository-format=docker --location="$REGION"

# Build das imagens (na raiz do repositório da aplicação)
gcloud builds submit ./backend \
  --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images/api:latest"
gcloud builds submit ./backend \
  --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images/agents:latest"
```

### 8.2 Deploy do serviço de API

```bash
gcloud run deploy ib-api \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images/api:latest" \
  --service-account="$SA_API" \
  --vpc-connector=ib-connector --vpc-egress=private-ranges-only \
  --add-cloudsql-instances="${PROJECT_ID}:${REGION}:ib-postgres" \
  --set-secrets="DATABASE_URL=db-url:latest,JWT_KEY=jwt-signing-key:latest" \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID},REGION=${REGION}" \
  --min-instances=0 --max-instances=20 --cpu=1 --memory=1Gi \
  --allow-unauthenticated   # a autorização é feita na app (JWT)
```

### 8.3 Deploy do serviço de agentes (ADK) + push Pub/Sub

```bash
gcloud run deploy ib-agents \
  --image "${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images/agents:latest" \
  --service-account="$SA_AGENTS" \
  --vpc-connector=ib-connector --vpc-egress=private-ranges-only \
  --add-cloudsql-instances="${PROJECT_ID}:${REGION}:ib-postgres" \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=us-central1" \
  --no-allow-unauthenticated \
  --min-instances=0 --max-instances=30 --cpu=2 --memory=2Gi

# Assinatura push do Pub/Sub -> serviço de agentes (com OIDC)
IB_AGENTS_URL="$(gcloud run services describe ib-agents --format='value(status.url)')"
gcloud pubsub subscriptions create analysis-push \
  --topic=analysis-requested \
  --push-endpoint="${IB_AGENTS_URL}/pubsub/analysis" \
  --push-auth-service-account="$SA_AGENTS"
```

> **Alternativa gerenciada — Vertex AI Agent Engine:** em vez de empacotar o ADK
> em Cloud Run, é possível publicar os agentes no **Agent Engine** (runtime
> gerenciado do Vertex AI para agentes ADK), que cuida de escala, sessões e
> observabilidade. Trade-off: menos controle de infra, porém menos ops. Comece
> com Cloud Run (portável) e avalie Agent Engine quando o volume crescer.

---

## 9. Borda: Load Balancer + Cloud Armor + domínio

```bash
# Política de segurança (rate limit + WAF básico)
gcloud compute security-policies create ib-armor \
  --description="WAF Inclua Beauty"
gcloud compute security-policies rules create 1000 \
  --security-policy=ib-armor \
  --expression="true" \
  --action=rate-based-ban --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 --ban-duration-sec=300 \
  --conform-action=allow --exceed-action=deny-429 \
  --enforce-on-key=IP
```

Mapeie o domínio (ex.: `app.incluabeauty.ai`) via **Serverless NEG** +
HTTPS Load Balancer com certificado gerenciado, associando a `ib-api` e servindo
o frontend React por Cloud Storage/CDN ou pelo próprio Cloud Run.

---

## 10. Infraestrutura como código (Terraform)

Toda a infra acima deve viver em Terraform para reprodutibilidade. Exemplo
reduzido do módulo principal:

```hcl
# infra/terraform/main.tf
terraform {
  required_providers { google = { source = "hashicorp/google", version = "~> 5.0" } }
  backend "gcs" { bucket = "inclua-beauty-tfstate" prefix = "prod" }
}
provider "google" { project = var.project_id  region = var.region }

resource "google_sql_database_instance" "pg" {
  name             = "ib-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  settings {
    tier              = "db-custom-2-7680"
    availability_type = "REGIONAL"
    ip_configuration { ipv4_enabled = false  private_network = google_compute_network.vpc.id }
  }
}

resource "google_cloud_run_v2_service" "api" {
  name     = "ib-api"
  location = var.region
  template {
    service_account = google_service_account.api.email
    scaling { min_instance_count = 0  max_instance_count = 20 }
    containers { image = var.api_image }
    vpc_access { connector = google_vpc_access_connector.conn.id  egress = "PRIVATE_RANGES_ONLY" }
  }
}
# ... run agents, pubsub, storage, secrets, iam, armor, lb ...
```

```bash
cd infra/terraform
terraform init
terraform plan  -var project_id=$PROJECT_ID -var region=$REGION
terraform apply -var project_id=$PROJECT_ID -var region=$REGION
```

---

## 11. CI/CD (Cloud Build)

```yaml
# cloudbuild.yaml
steps:
  - name: python:3.12
    entrypoint: bash
    args: ["-c", "pip install -e ./backend[dev] && pytest -q && ruff check ."]
  - name: gcr.io/cloud-builders/docker
    args: ["build","-t","$_REG/api:$SHORT_SHA","./backend"]
  - name: gcr.io/cloud-builders/docker
    args: ["push","$_REG/api:$SHORT_SHA"]
  - name: gcr.io/google.com/cloudsdktool/cloud-sdk
    entrypoint: gcloud
    args: ["run","deploy","ib-api","--image","$_REG/api:$SHORT_SHA","--region","$_REGION"]
substitutions:
  _REG: "southamerica-east1-docker.pkg.dev/$PROJECT_ID/ib-images"
  _REGION: "southamerica-east1"
options: { logging: CLOUD_LOGGING_ONLY }
```

Inclua no pipeline os **evals do ADK** (casos de aceite: perfume, baixa visão,
destreza) como gate de qualidade antes do deploy em `prod`.

---

## 12. Carga inicial da base normativa (RAG)

```bash
# Script que fatia normas (WCAG, LBI, ANVISA, EAA, ISO/NBR), gera embeddings
# com text-embedding-004 e insere em standard_chunks. Cada item recebe
# 'status' (confirmada/hipótese/...) e 'jurisdiction'.
python -m app.scripts.seed_standards \
  --source docs/normas/ --jurisdiction BR --embed-model text-embedding-004
```

> **Governança normativa (RF-016/RNF-015):** cada norma entra com status e nota
> de aplicabilidade; revisão por especialista antes de "confirmada". A IA nunca
> emite conformidade legal definitiva sem validação humana.

---

## 13. Observabilidade e operação

```bash
# Ver traces de agentes (Cloud Trace) e logs por análise
gcloud logging read \
  'resource.type=cloud_run_revision AND jsonPayload.analysis_run_id="<ID>"' \
  --limit=50

# Exportar billing para BigQuery (custo por tenant/feature) — via console:
# Billing > Billing export > BigQuery export
```

Crie **SLOs** no Cloud Monitoring: latência p95 da análise < 60s, taxa de erro
< 1%, e alerta de custo/análise acima do teto definido (RNF-012).

---

## 14. Utilização da plataforma (jornada do cliente)

Depois de implantada, o uso segue o fluxo funcional do produto:

1. **Onboarding**: admin cria a **organização** e convida usuários por papel
   (gestor de marca, designer, especialista, regulatório, testador PcD).
2. **Novo projeto**: informa nome, marca, categoria, país/região e objetivo.
3. **Cadastro do produto**: preenche nome, descrição, materiais, tipo de tampa,
   público-alvo e **faz upload das imagens** (frasco, rótulo, tampa, caixa).
4. **Executar análise**: a plataforma classifica a categoria, decompõe os
   componentes (usuário confirma/corrige) e dispara a malha de agentes.
5. **Resultado** (em < 60s no MVP): checklist com status por item, **score
   0–100** por dimensão, recomendações mín/interm/premium, matriz normativa com
   status de cada norma e prompts de mockup.
6. **Revisão humana**: itens marcados "A validar" vão para o especialista; só
   após o parecer o relatório vira "final".
7. **Exportação**: PDF/DOCX/HTML/JSON/CSV ou link compartilhável; versões
   executiva (diretoria) e regulatória (compliance).
8. **Feedback PcD**: registro de testes com pessoas com deficiência anexado como
   evidência de co-design.

### 14.1 Exemplo de chamada de API

```bash
TOKEN="<jwt-do-login>"
API="$(gcloud run services describe ib-api --format='value(status.url)')"

# Criar produto e disparar análise
curl -s -X POST "$API/analysis-runs" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id":"prod_123","profiles":["baixa_visao","destreza_reduzida"]}'

# Buscar score e recomendações
curl -s "$API/analysis-runs/run_456/score"           -H "Authorization: Bearer $TOKEN"
curl -s "$API/analysis-runs/run_456/recommendations" -H "Authorization: Bearer $TOKEN"

# Gerar e baixar relatório
curl -s -X POST "$API/reports" -H "Authorization: Bearer $TOKEN" \
  -d '{"analysis_run_id":"run_456","format":"pdf"}'
```

---

## 15. Checklist de go-live

- [ ] Budget + alertas de billing ativos
- [ ] APIs habilitadas e SAs com papéis mínimos
- [ ] Cloud SQL REGIONAL + backups automáticos + pgvector
- [ ] Secrets no Secret Manager (nada em código)
- [ ] Cloud Run com VPC connector e egress privado
- [ ] Vertex AI validado na região; roteamento Flash/Pro configurado
- [ ] Cloud Armor + HTTPS LB + domínio + certificado gerenciado
- [ ] Terraform aplicando 100% da infra; state no GCS
- [ ] CI/CD com testes + evals de agentes como gate
- [ ] Base normativa carregada com status e revisão de especialista
- [ ] SLOs, dashboards e alerta de custo/análise
- [ ] DPA/LGPD, retenção e política de exclusão definidas

---

## 16. Estimativa de custo de infraestrutura base (mensal, ordem de grandeza)

> Valores de referência para dimensionamento; **valide na calculadora oficial do
> GCP** na data. Não inclui custo de inferência (ver doc 04).

| Item | Config | Custo/mês aprox. (USD) |
|---|---|---:|
| Cloud SQL PG (2 vCPU / 7,5GB, REGIONAL) | HA + 50GB | 200–350 |
| Cloud Run (api+agents, tráfego moderado) | escala a zero | 30–150 |
| Cloud Storage + egress | 100–500 GB | 10–40 |
| Load Balancer + Cloud Armor | 1 regra | 25–40 |
| Pub/Sub, Secret Manager, Logs/Trace | uso baixo | 10–30 |
| **Subtotal infra fixa** | | **~275–610/mês** |

A inferência (Vertex AI/Gemini) é **variável por análise** e detalhada no
documento 04 (unit economics e precificação).
