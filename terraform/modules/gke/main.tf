provider "google" {
  alias   = var.provider_alias
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "primary" {
  provider       = google.${var.provider_alias}
  name           = var.name
  location       = var.region
  network        = var.network
  subnetwork     = var.subnetwork
  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {}
}

resource "google_container_node_pool" "primary_nodes" {
  provider   = google.${var.provider_alias}
  name       = "${var.name}-node-pool"
  cluster    = google_container_cluster.primary.name
  location   = var.region

  node_config {
    machine_type = "e2-medium"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
  }

  initial_node_count = 2
}
