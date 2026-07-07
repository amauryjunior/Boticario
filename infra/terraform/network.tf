# VPC privada + conector serverless + peering para Cloud SQL (IP privado).
resource "google_compute_network" "vpc" {
  name                    = "ib-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.enabled]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "ib-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_vpc_access_connector" "connector" {
  name          = "ib-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"
  depends_on    = [google_project_service.enabled]
}

# Range reservado para o peering do Service Networking (Cloud SQL privado).
resource "google_compute_global_address" "private_ip" {
  name          = "ib-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}
