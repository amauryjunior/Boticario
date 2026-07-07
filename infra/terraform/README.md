# Infra Terraform — Inclua Beauty AI (GCP)

Provisiona toda a infraestrutura de produção: APIs, VPC privada, Cloud SQL
(PostgreSQL HA), Cloud Run (API + agentes), Pub/Sub (com DLQ e push OIDC),
Cloud Storage, Secret Manager, Artifact Registry e IAM least-privilege.

## Pré-requisitos

- `terraform >= 1.6`, `gcloud` autenticado, projeto GCP com billing ativo.
- (Recomendado) bucket GCS para o state remoto; descomente o bloco `backend "gcs"`
  em `versions.tf`.

## Uso

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # edite (ou use TF_VAR_*)

export TF_VAR_db_password='...'      # não commite segredos
export TF_VAR_jwt_secret='...'

terraform init
terraform plan
terraform apply
```

### Ordem recomendada (bootstrap x imagens)

1. `apply` inicial com as imagens placeholder (default das variáveis) para criar
   Artifact Registry, Cloud SQL, rede etc.
2. Build/push das imagens `api` e `agents` (ver CI/CD em `cloudbuild.yaml`).
3. `apply` novamente com `-var api_image=... -var agents_image=...` apontando para
   o Artifact Registry.

## Pós-provisionamento

Habilite a extensão pgvector e crie a tabela de RAG (via Cloud SQL Studio ou
Auth Proxy):

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

As tabelas da aplicação são criadas automaticamente pelo backend no startup
(`Base.metadata.create_all`) / migrations Alembic.

## Recursos criados

| Arquivo | Recursos |
|---|---|
| `apis.tf` | habilitação das APIs GCP |
| `network.tf` | VPC, subnet, conector serverless, peering para Cloud SQL |
| `database.tf` | Cloud SQL PostgreSQL 16 (REGIONAL) + DB + usuário |
| `storage.tf` | buckets de uploads/relatórios + Artifact Registry |
| `pubsub.tf` | tópico `analysis-requested`, subscription push OIDC, DLQ |
| `secrets.tf` | `db-url` e `jwt-signing-key` no Secret Manager |
| `iam.tf` | service accounts `sa-api`/`sa-agents` + papéis mínimos |
| `cloudrun.tf` | serviços `ib-api` (público) e `ib-agents` (privado) |
| `outputs.tf` | URLs, connection name, bucket, Artifact Registry |

> Custos: ver estimativa em `docs/inclua-beauty/02-instalacao-gcp.md` §16.
> Segurança: `deletion_protection` ativo no Cloud SQL; egress privado no Run.
