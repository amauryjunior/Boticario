#!/usr/bin/env bash
# Deploy de um comando da Inclua Beauty AI no Google Cloud.
#
# Pré-requisitos: gcloud autenticado (gcloud auth login && gcloud auth
# application-default login), terraform >= 1.6 e permissão de Owner/Editor no
# projeto. Uso:
#
#   PROJECT_ID=meu-projeto REGION=southamerica-east1 \
#   TF_VAR_db_password='...' TF_VAR_jwt_secret='...' \
#   ./scripts/deploy.sh
#
set -euo pipefail

# ---- Configuração -----------------------------------------------------------
PROJECT_ID="${PROJECT_ID:?defina PROJECT_ID}"
REGION="${REGION:-southamerica-east1}"
VERTEX_LOCATION="${VERTEX_LOCATION:-us-central1}"
TAG="${TAG:-$(date +%Y%m%d-%H%M%S)}"
AR="${REGION}-docker.pkg.dev/${PROJECT_ID}/ib-images"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="${ROOT}/infra/terraform"

log() { printf '\033[1;35m[deploy]\033[0m %s\n' "$*"; }

require() { command -v "$1" >/dev/null 2>&1 || { echo "faltando: $1"; exit 1; }; }
require gcloud
require terraform

: "${TF_VAR_db_password:?defina TF_VAR_db_password}"
: "${TF_VAR_jwt_secret:?defina TF_VAR_jwt_secret}"

export TF_VAR_project_id="$PROJECT_ID"
export TF_VAR_region="$REGION"
export TF_VAR_vertex_location="$VERTEX_LOCATION"

gcloud config set project "$PROJECT_ID" >/dev/null

# ---- Fase 1: infra base (Artifact Registry, SQL, rede, etc.) ----------------
log "Fase 1/4: terraform apply (infra base, imagens placeholder)"
terraform -chdir="$TF_DIR" init -input=false
terraform -chdir="$TF_DIR" apply -input=false -auto-approve \
  -target=google_project_service.enabled \
  -target=google_artifact_registry_repository.images

# ---- Fase 2: build e push das imagens ---------------------------------------
log "Fase 2/4: build + push das imagens (Cloud Build) tag=${TAG}"
gcloud builds submit "${ROOT}/backend" --tag "${AR}/api:${TAG}"
gcloud builds submit "${ROOT}/backend" --tag "${AR}/agents:${TAG}"

# ---- Fase 3: apply completo com as imagens reais ----------------------------
log "Fase 3/4: terraform apply (stack completo com imagens ${TAG})"
terraform -chdir="$TF_DIR" apply -input=false -auto-approve \
  -var "api_image=${AR}/api:${TAG}" \
  -var "agents_image=${AR}/agents:${TAG}"

# ---- Fase 4: pós-deploy -----------------------------------------------------
log "Fase 4/4: habilitando pgvector no Cloud SQL"
CONNECTION_NAME="$(terraform -chdir="$TF_DIR" output -raw sql_connection_name)"
cat <<EOF

  Rode uma vez (via Cloud SQL Studio ou Auth Proxy) para habilitar o RAG:
    CREATE EXTENSION IF NOT EXISTS vector;
  Instância: ${CONNECTION_NAME}

EOF

API_URL="$(terraform -chdir="$TF_DIR" output -raw api_url)"
log "Deploy concluído."
log "API:  ${API_URL}"
log "Docs: ${API_URL}/docs"
log "Health: $(curl -s "${API_URL}/health" || echo 'aguardando cold start...')"
