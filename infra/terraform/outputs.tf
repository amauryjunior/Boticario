output "api_url" {
  value       = google_cloud_run_v2_service.api.uri
  description = "URL pública da API."
}

output "agents_url" {
  value       = google_cloud_run_v2_service.agents.uri
  description = "URL do serviço de agentes (privado)."
}

output "sql_connection_name" {
  value       = google_sql_database_instance.pg.connection_name
  description = "Connection name do Cloud SQL."
}

output "uploads_bucket" {
  value = google_storage_bucket.uploads.name
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}
