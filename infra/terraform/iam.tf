# Service accounts e papéis mínimos (least privilege).
resource "google_service_account" "api" {
  account_id   = "sa-api"
  display_name = "Inclua Beauty API"
}

resource "google_service_account" "agents" {
  account_id   = "sa-agents"
  display_name = "Inclua Beauty Agents"
}

locals {
  api_roles = [
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/pubsub.publisher",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
  ]
  agents_roles = [
    "roles/aiplatform.user",
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
  ]
}

resource "google_project_iam_member" "api" {
  for_each = toset(local.api_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "agents" {
  for_each = toset(local.agents_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.agents.email}"
}

# Permite ao Pub/Sub gerar tokens OIDC para o push.
resource "google_project_iam_member" "pubsub_token" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

data "google_project" "this" {
  project_id = var.project_id
}
