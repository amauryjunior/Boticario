# Buckets de uploads e relatórios + Artifact Registry.
resource "google_storage_bucket" "uploads" {
  name                        = "${var.project_id}-uploads"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  versioning { enabled = true }
}

resource "google_storage_bucket" "reports" {
  name                        = "${var.project_id}-reports"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
}

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "ib-images"
  format        = "DOCKER"
  depends_on    = [google_project_service.enabled]
}
