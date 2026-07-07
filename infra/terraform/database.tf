# Cloud SQL PostgreSQL (HA regional, IP privado).
resource "google_sql_database_instance" "pg" {
  name                = "ib-postgres"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = true
  depends_on          = [google_service_networking_connection.private_vpc]

  settings {
    tier              = var.db_tier
    availability_type = "REGIONAL"
    disk_autoresize   = true
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
  # pgvector é habilitado por `CREATE EXTENSION vector;` após o provisionamento
  # (ver infra/terraform/README.md).
}

resource "google_sql_database" "app" {
  name     = "incluabeauty"
  instance = google_sql_database_instance.pg.name
}

resource "google_sql_user" "app" {
  name     = "ib_app"
  instance = google_sql_database_instance.pg.name
  password = var.db_password
}
