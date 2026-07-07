# Serviços Cloud Run: API (pública, authZ na app) e agentes (privado, push).
resource "google_cloud_run_v2_service" "api" {
  name       = "ib-api"
  location   = var.region
  depends_on = [google_project_service.enabled]

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = 0
      max_instance_count = 20
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.pg.connection_name]
      }
    }

    containers {
      image = var.api_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "ANALYSIS_MODE"
        value = "async"
      }
      env {
        name  = "QUEUE_BACKEND"
        value = "pubsub"
      }
      env {
        name  = "ANALYSIS_ENGINE"
        value = var.analysis_engine
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.uploads.name
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.vertex_location
      }
      env {
        name  = "SEED_DEMO"
        value = "false"
      }
    }
  }
}

resource "google_cloud_run_v2_service" "agents" {
  name       = "ib-agents"
  location   = var.region
  depends_on = [google_project_service.enabled]

  template {
    service_account = google_service_account.agents.email

    scaling {
      min_instance_count = 0
      max_instance_count = 30
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.pg.connection_name]
      }
    }

    containers {
      image = var.agents_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "ANALYSIS_ENGINE"
        value = var.analysis_engine
      }
      env {
        name  = "GCS_BUCKET"
        value = google_storage_bucket.uploads.name
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.vertex_location
      }
    }
  }
}

# API pública (a autorização é feita na aplicação via JWT/RBAC).
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Agentes: apenas a SA de agentes pode invocar (push OIDC do Pub/Sub).
resource "google_cloud_run_v2_service_iam_member" "agents_invoker" {
  name     = google_cloud_run_v2_service.agents.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.agents.email}"
}
