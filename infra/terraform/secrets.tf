# Segredos: URL do banco e chave JWT.
resource "google_secret_manager_secret" "db_url" {
  secret_id  = "db-url"
  replication { auto {} }
  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret = google_secret_manager_secret.db_url.id
  # Conexão via Cloud SQL socket (psycopg + host=/cloudsql/INSTANCE)
  secret_data = "postgresql+psycopg://ib_app:${var.db_password}@/incluabeauty?host=/cloudsql/${google_sql_database_instance.pg.connection_name}"
}

resource "google_secret_manager_secret" "jwt" {
  secret_id  = "jwt-signing-key"
  replication { auto {} }
  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_version" "jwt" {
  secret      = google_secret_manager_secret.jwt.id
  secret_data = var.jwt_secret
}
