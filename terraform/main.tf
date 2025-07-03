resource "google_compute_network" "vpc_network" {
  name                    = var.network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet_region1" {
  name          = "${var.network_name}-${var.region1}"
  ip_cidr_range = "10.10.0.0/16"
  region        = var.region1
  network       = google_compute_network.vpc_network.id
}

resource "google_compute_subnetwork" "subnet_region2" {
  name          = "${var.network_name}-${var.region2}"
  ip_cidr_range = "10.20.0.0/16"
  region        = var.region2
  network       = google_compute_network.vpc_network.id
}

module "gke_region1" {
  source         = "./modules/gke"
  project_id     = var.project_id
  name           = "${var.cluster_name_prefix}-${var.region1}"
  region         = var.region1
  network        = google_compute_network.vpc_network.name
  subnetwork     = google_compute_subnetwork.subnet_region1.name
  provider_alias = "region1"
}

module "gke_region2" {
  source         = "./modules/gke"
  project_id     = var.project_id
  name           = "${var.cluster_name_prefix}-${var.region2}"
  region         = var.region2
  network        = google_compute_network.vpc_network.name
  subnetwork     = google_compute_subnetwork.subnet_region2.name
  provider_alias = "region2"
}
