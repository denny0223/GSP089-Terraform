locals {
  has_alert_email = trimspace(var.alert_email) != ""
}

resource "google_monitoring_uptime_check_config" "lamp" {
  display_name = "Lamp Uptime Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/"
    port           = 80
    request_method = "GET"
    use_ssl        = false
    validate_ssl   = false
  }

  monitored_resource {
    type = "uptime_url"

    labels = {
      project_id = var.project_id
      host       = google_compute_instance.lamp.network_interface[0].access_config[0].nat_ip
    }
  }

  depends_on = [
    google_compute_instance.lamp
  ]
}

resource "google_monitoring_notification_channel" "email" {
  count = local.has_alert_email ? 1 : 0

  display_name = "GSP089 Email Channel"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "inbound_traffic" {
  display_name = "Inbound Traffic Alert"
  combiner     = "OR"
  enabled      = true

  documentation {
    content   = "Inbound Traffic Alert"
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "VM inbound network traffic above 500"

    condition_threshold {
      filter = "resource.type = \"gce_instance\" AND metric.type = \"agent.googleapis.com/interface/traffic\" AND resource.labels.instance_id = \"${google_compute_instance.lamp.instance_id}\""

      comparison      = "COMPARISON_GT"
      threshold_value = 500
      duration        = "60s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }

      trigger {
        count = 1
      }
    }
  }

  notification_channels = local.has_alert_email ? [
    google_monitoring_notification_channel.email[0].name
  ] : []

  depends_on = [
    google_compute_instance.lamp
  ]
}

resource "google_monitoring_dashboard" "lamp" {
  dashboard_json = jsonencode({
    displayName = "Cloud Monitoring LAMP Qwik Start Dashboard"

    gridLayout = {
      columns = 2

      widgets = [
        {
          title = "CPU Load"

          xyChart = {
            dataSets = [
              {
                plotType = "LINE"

                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"gce_instance\" AND metric.type=\"agent.googleapis.com/cpu/load_1m\""

                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
              }
            ]

            yAxis = {
              label = "CPU load"
              scale = "LINEAR"
            }
          }
        },
        {
          title = "Received Packets"

          xyChart = {
            dataSets = [
              {
                plotType = "LINE"

                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"gce_instance\" AND metric.type=\"compute.googleapis.com/instance/network/received_packets_count\""

                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
              }
            ]

            yAxis = {
              label = "Packets / sec"
              scale = "LINEAR"
            }
          }
        }
      ]
    }
  })

  depends_on = [
    google_compute_instance.lamp
  ]
}
