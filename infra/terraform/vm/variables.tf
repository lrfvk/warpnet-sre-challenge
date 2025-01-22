variable "project_id" {
  description = "The GCP project ID"
  type        = string
  default     = "warpnet-447820"
}

variable "region" {
  description = "The GCP region for the VM"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "The GCP zone for the VM"
  type        = string
  default     = "europe-west1-b"
}

variable "instance_name" {
  description = "The name of the VM instance"
  type        = string
  default     = "warpnet-app-vm"
}

variable "machine_type" {
  description = "The machine type for the VM"
  type        = string
  default     = "e2-micro" # Cheapest machine type
}

variable "boot_image" {
  description = "The image to use for the boot disk"
  type        = string
  default     = "debian-cloud/debian-11" # Lightweight OS for Flask app
}

variable "flask_app_code" {
  description = "The code for the Flask app"
  type        = string
  default     = <<EOT
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask running on a VM!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
EOT
}
