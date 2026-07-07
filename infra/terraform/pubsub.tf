# Fila de análise (Pub/Sub) com push OIDC para o serviço de agentes + DLQ.
resource "google_pubsub_topic" "analysis_requested" {
  name       = "analysis-requested"
  depends_on = [google_project_service.enabled]
}

resource "google_pubsub_topic" "analysis_dlq" {
  name = "analysis-dlq"
}

resource "google_pubsub_subscription" "analysis_push" {
  name  = "analysis-push"
  topic = google_pubsub_topic.analysis_requested.name

  ack_deadline_seconds = 120

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.agents.uri}/api/v1/internal/pubsub/analysis"
    oidc_token {
      service_account_email = google_service_account.agents.email
    }
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.analysis_dlq.id
    max_delivery_attempts = 5
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}
