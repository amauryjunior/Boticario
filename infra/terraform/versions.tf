terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.30"
    }
  }
  # Recomendado: manter o state remoto no GCS (crie o bucket antes).
  # backend "gcs" {
  #   bucket = "inclua-beauty-tfstate"
  #   prefix = "prod"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
