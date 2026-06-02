variable "project_id" {
  type        = string
  description = "Qwiklabs temporary Google Cloud project ID."
}

variable "region" {
  type        = string
  description = "Google Cloud region."
  default     = "us-central1"
}

variable "zone" {
  type        = string
  description = "Google Cloud zone."
  default     = "us-central1-b"
}

variable "vm_name" {
  type        = string
  description = "Compute Engine VM name required by the lab."
  default     = "lamp-1-vm"
}

variable "machine_type" {
  type        = string
  description = "Machine type required by the lab."
  default     = "e2-medium"
}

variable "alert_email" {
  type        = string
  description = "Optional email notification channel for alert policy. Leave empty if you do not want email notification."
  default     = ""
}
