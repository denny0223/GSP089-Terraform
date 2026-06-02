# AGENTS.md

This repository contains a Terraform implementation of Google Cloud Skills Boost lab GSP089, "Cloud Monitoring: Qwik Start".

## Documentation standards

- Write `README.md` for students who are about to perform the lab.
- Use Traditional Chinese suitable for readers in Taiwan in `README.md`.
- Keep README content action-oriented: setup, commands, expected results, validation, cleanup, and troubleshooting.
- Do not include conversation history, implementation rationale aimed at maintainers, or references to prior assistant/user discussion in student-facing docs.
- Keep this `AGENTS.md` file in English.

## Lab constraints

Skills Boost lab values can change between sessions:

- `project_id` changes on every lab run.
- `region` and `zone` may change. The current lab instructions use `us-central1` and `us-central1-b`.
- Student accounts, passwords, project ids, and other temporary credentials must never be committed.

Tracked files must not contain real Qwiklabs credentials or a real Qwiklabs project id. Use placeholders such as `qwiklabs-gcp-xx-xxxxxxxxxxxx`.

## Terraform layout

- `versions.tf`: Terraform version and provider requirements.
- `variables.tf`: input variables and defaults.
- `main.tf`: Compute Engine, firewall, and VM startup script.
- `monitoring.tf`: Monitoring uptime check, notification channel, alert policy, and dashboard.
- `outputs.tf`: values students use to verify the lab.
- `samples/opentelemetry/`: optional OpenTelemetry follow-up exercise files.
- `terraform.tfvars.example`: safe example input values.

`terraform.tfvars` is local to each lab session and must stay ignored.

## Expected resources

The Terraform configuration should create:

- VM: `lamp-1-vm`
- HTTP ingress firewall rule for TCP 80
- Apache installed through startup script
- Google Cloud Ops Agent installed through startup script
- Uptime check: `Lamp Uptime Check`
- Alert policy: `Inbound Traffic Alert`
- Optional email notification channel controlled by `alert_email`
- Dashboard: `Cloud Monitoring LAMP Qwik Start Dashboard`

Preserve lab-required resource names unless the lab instructions change.

## Maintenance guidance

- Prefer variables for session-specific values.
- Keep commands copy-paste friendly for Cloud Shell.
- Use official provider resources instead of shelling out from Terraform.
- Keep the VM startup script focused on guest setup: Apache, PHP, and Ops Agent.
- Keep OpenTelemetry samples small, dependency-light, and runnable from Cloud Shell or the lab VM.
- Be careful when changing Monitoring metric type strings; dashboards and alert policies depend on exact metric names.
- Run `terraform fmt` after editing Terraform files.
- Run `terraform validate` when provider plugins are available.
- Keep `.terraform.lock.hcl` committed for this root module when it exists.
- Do not commit `.terraform/`, state files, local `terraform.tfvars`, swap files, or credentials.
