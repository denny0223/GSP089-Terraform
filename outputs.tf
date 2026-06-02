output "project_id" {
  value = var.project_id
}

output "zone" {
  value = var.zone
}

output "vm_name" {
  value = google_compute_instance.lamp.name
}

output "vm_external_ip" {
  value = google_compute_instance.lamp.network_interface[0].access_config[0].nat_ip
}

output "apache_url" {
  value = "http://${google_compute_instance.lamp.network_interface[0].access_config[0].nat_ip}"
}

output "uptime_check_name" {
  value = google_monitoring_uptime_check_config.lamp.display_name
}

output "alert_policy_name" {
  value = google_monitoring_alert_policy.inbound_traffic.display_name
}

output "dashboard_name" {
  value = "Cloud Monitoring LAMP Qwik Start Dashboard"
}
