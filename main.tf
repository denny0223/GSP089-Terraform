data "google_compute_network" "default" {
  name = "default"
}

resource "google_compute_firewall" "allow_http" {
  name    = "default-allow-http"
  network = data.google_compute_network.default.name

  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

resource "google_compute_instance" "lamp" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["http-server"]

  boot_disk {
    initialize_params {
      image = "projects/debian-cloud/global/images/family/debian-12"
      size  = 10
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = data.google_compute_network.default.self_link

    access_config {
      # Ephemeral external IP, same as the Console default.
    }
  }

  service_account {
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    exec > >(tee /var/log/gsp089-startup.log) 2>&1

    echo "=== Installing Apache ==="
    apt-get update

    # Debian 12 normally uses the php metapackage, not php7.0.
    # The lab text mentions php7.0, but this fallback is more robust.
    DEBIAN_FRONTEND=noninteractive apt-get install -y apache2 php || \
      DEBIAN_FRONTEND=noninteractive apt-get install -y apache2

    systemctl enable apache2
    systemctl restart apache2

    echo "=== Installing Google Cloud Ops Agent ==="
    cd /tmp
    curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
    bash add-google-cloud-ops-agent-repo.sh --also-install

    systemctl status google-cloud-ops-agent"*" --no-pager || true

    echo "=== Startup script completed ==="
  EOT

  depends_on = [
    google_compute_firewall.allow_http
  ]
}
