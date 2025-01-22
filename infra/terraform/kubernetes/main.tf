
data "google_client_config" "default" {}

module "gcp-network" {
  source  = "terraform-google-modules/network/google"
  version = ">= 7.5"

  project_id   = var.project_id
  network_name = var.network

  subnets = [
    {
      subnet_name   = var.subnetwork
      subnet_ip     = "10.0.0.0/17"
      subnet_region = var.region
    },
  ]

  secondary_ranges = {
    (var.subnetwork) = [
      {
        range_name    = var.ip_range_pods_name
        ip_cidr_range = "192.168.0.0/18"
      },
      {
        range_name    = var.ip_range_services_name
        ip_cidr_range = "192.168.64.0/18"
      },
    ]
  }
}


provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}
module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  version                    = "~> 35.0"
  project_id                 = var.project_id
  name                       = "warpnet-sre-cluster"
  regional                   = false
  zones                      = ["europe-west1-b"]
  network                    = module.gcp-network.network_name
  subnetwork                 = module.gcp-network.subnets_names[0]
  ip_range_pods              = var.ip_range_pods_name
  ip_range_services          = var.ip_range_services_name
  create_service_account     = true
  horizontal_pod_autoscaling = true

  node_pools = [
    {
      name         = "default-pool-001"
      machine_type = "e2-micro"
      min_count    = 1
      max_count    = 3
      disk_size_gb = 10
      disk_type    = "pd-standard"
      auto_upgrade = true
      auto_repair  = true
      preemptible  = true
    }
  ]
}
