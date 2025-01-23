terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.16.0"
    }
  }
  required_version = ">= 1.0"
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

resource "google_compute_instance" "ecorp_vm" {
  name         = "ecorp-vm"
  machine_type = var.machine_type

  # Tag for firewall rule
  tags = ["http-server"]

  # Use Container-Optimized OS
  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
    }
  }

  # Attach to default network with ephemeral external IP
  network_interface {
    network = "default"
    access_config {}
  }

  # Startup script to run Docker container
  metadata_startup_script = <<-EOF
    #!/bin/bash
    # On Container-Optimized OS, Docker is already installed.
    # Just pull and run your container on port 80:
    docker run -d -p 80:5050 lrfvk/ecorpapp
  EOF
}

resource "google_compute_firewall" "allow_http_https" {
  name    = "ecorp-allow-http-https"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  # Open port 80 and 443 to the world
  source_ranges = ["0.0.0.0/0"]

  # Target instances tagged with "http-server"
  target_tags = ["http-server"]
}
