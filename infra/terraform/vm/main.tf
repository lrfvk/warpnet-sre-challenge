# main.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_compute_instance" "warpnet_vm" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = var.boot_image
      size  = 10
    }
  }

  network_interface {
    network = "default"

    access_config {
      # Creates an external IP address
    }
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update
    apt-get install -y python3 python3-pip
    pip3 install flask

    # Copy app code from metadata or a storage bucket (example below uses metadata)
    echo "${var.flask_app_code}" > /app/app.py

    # Run the Flask application
    python3 /app/app.py &
  EOT
}

output "vm_external_ip" {
  value = google_compute_instance.warpnet_vm.network_interface[0].access_config[0].nat_ip
}

output "vm_name" {
  value = google_compute_instance.warpnet_vm.name
}
