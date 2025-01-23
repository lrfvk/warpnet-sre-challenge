output "ecorp_external_ip" {
  description = "The external IP address of the ecorp VM"
  value       = google_compute_instance.ecorp_vm.network_interface[0].access_config[0].nat_ip
}
