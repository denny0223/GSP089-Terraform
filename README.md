# GSP089：使用 Terraform 完成 Cloud Monitoring Lab

本 lab 會使用 Terraform 建立一台 Compute Engine VM，安裝 Apache 與 Google Cloud Ops Agent，並建立 Cloud Monitoring 的 uptime check、alert policy 和 dashboard。

完成後，你可以用這個 lab 觀察：

- Terraform 如何用程式碼建立 Google Cloud 資源
- VM 建立後如何自動安裝服務
- Cloud Monitoring 如何監控 VM 與網路流量
- Cloud Logging 如何顯示 VM 啟動、停止與服務狀態

## 建立的資源

Terraform 會建立下列資源：

- Compute Engine VM：`lamp-1-vm`
- HTTP 防火牆規則：允許外部連線到 TCP 80
- Apache HTTP Server
- Google Cloud Ops Agent
- Uptime check：`Lamp Uptime Check`
- Alert policy：`Inbound Traffic Alert`
- Monitoring dashboard：`Cloud Monitoring LAMP Qwik Start Dashboard`
- Dashboard widgets：`CPU Load`、`Received Packets`

## 開始前

請使用 Google Cloud Skills Boost lab 提供的帳號登入 Google Cloud Console，並開啟 Cloud Shell。

確認目前登入帳號與專案：

```bash
gcloud auth list
gcloud config list project
```

確認 Terraform 可用：

```bash
terraform version
```

如果 Cloud Shell 顯示找不到 `terraform` 指令，請依照 HashiCorp 官方文件的 [Install Terraform](https://developer.hashicorp.com/terraform/install) 說明安裝。安裝完成後，再重新執行 `terraform version` 確認。

## 設定 lab 環境

每次啟動 Skills Boost lab 時，Google Cloud project id 可能不同。請先設定本 lab 使用的 region 與 zone：

```bash
gcloud config set compute/region "us-central1"
gcloud config set compute/zone "us-central1-b"
```

接著產生本次 lab 專用的 `terraform.tfvars`：

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="$(gcloud config get-value compute/region)"
ZONE="$(gcloud config get-value compute/zone)"

cat > terraform.tfvars <<EOF
project_id   = "${PROJECT_ID}"
region       = "${REGION}"
zone         = "${ZONE}"
vm_name      = "lamp-1-vm"
machine_type = "e2-medium"
alert_email  = ""
EOF
```

`terraform.tfvars` 會提供 Terraform 需要的變數值。這個檔案只屬於本次 lab，不需要提交到版本控制。

如果要讓 alert policy 寄送 email，把 `terraform.tfvars` 裡的 `alert_email` 改成你的 email：

```hcl
alert_email = "you@example.com"
```

啟用需要的 Google Cloud API：

```bash
gcloud services enable \
  compute.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

## 執行 Terraform

初始化 Terraform provider：

```bash
terraform init
```

查看 Terraform 準備建立的資源：

```bash
terraform plan
```

建立資源：

```bash
terraform apply
```

Terraform 會列出即將建立的資源。確認內容後輸入 `yes`。

建立完成後，取得 Apache 網址：

```bash
terraform output apache_url
```

用瀏覽器開啟輸出的網址。如果看到 Apache 預設頁面，代表 VM、Apache 和 HTTP 防火牆已正常運作。

## 對照 lab 任務

### 工作 1：建立 Compute Engine VM

Terraform 會建立 `lamp-1-vm`：

- Machine type：`e2-medium`
- Boot disk：Debian 12
- Network：default network
- External IP：ephemeral external IP
- Network tag：`http-server`

HTTP 防火牆規則也會一併建立，對應 Console 建立 VM 時的「允許 HTTP 流量」。

### 工作 2：安裝 Apache 與 Ops Agent

VM 建立後會執行 startup script，自動完成：

- 更新 apt 套件清單
- 安裝 `apache2` 與 `php`
- 啟用並重啟 Apache
- 安裝 Google Cloud Ops Agent

查看 startup script 記錄：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "sudo tail -n 80 /var/log/gsp089-startup.log"
```

確認 Apache 狀態：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "sudo systemctl status apache2 --no-pager"
```

確認 Ops Agent 狀態：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command 'sudo systemctl status "google-cloud-ops-agent*"'
```

### 工作 3：建立 uptime check

Terraform 會建立 `Lamp Uptime Check`，每 60 秒用 HTTP 檢查 VM 外部 IP。

到 Console 查看結果：

```text
Navigation menu > Monitoring > Uptime checks
```

Uptime check 建立後通常需要等待幾分鐘，狀態才會完整顯示。

### 工作 4：建立 alert policy

Terraform 會建立 `Inbound Traffic Alert`，監控 Ops Agent 的網路流量指標：

```text
agent.googleapis.com/interface/traffic
```

門檻值為大於 `500`，重新測試週期為 `60s`。

如果 `alert_email` 有設定 email，Terraform 也會建立 email notification channel 並掛到 alert policy。

### 工作 5：建立 dashboard 與圖表

Terraform 會建立 dashboard：

```text
Cloud Monitoring LAMP Qwik Start Dashboard
```

Dashboard 內有兩張 line chart：

- `CPU Load`：CPU 1 分鐘負載
- `Received Packets`：收到的網路封包數

到 Console 查看 dashboard：

```text
Navigation menu > Monitoring > Dashboards
```

Ops Agent 指標剛開始可能不會立刻出現，請等待幾分鐘後重新整理頁面。

### 工作 6：查看 logs

到 Logs Explorer 查看 VM logs：

```text
Navigation menu > Logging > Logs Explorer
```

選擇資源：

```text
VM instance > lamp-1-vm
```

也可以用 Cloud Shell 查最近的 VM logs：

```bash
gcloud logging read \
  'resource.type="gce_instance" AND resource.labels.instance_id!=""' \
  --limit=20 \
  --format="table(timestamp,logName.basename(),textPayload)"
```

### 工作 7：觀察 VM 停止與啟動

停止 VM：

```bash
gcloud compute instances stop lamp-1-vm --zone "$(gcloud config get-value compute/zone)"
```

啟動 VM：

```bash
gcloud compute instances start lamp-1-vm --zone "$(gcloud config get-value compute/zone)"
```

VM 停止與啟動後，回到 Monitoring 和 Logging 觀察：

- Uptime check 狀態變化
- Logs Explorer 裡的 VM 事件
- Alerting 頁面的 incident 或 activity

## 延伸：用 OpenTelemetry 產生應用程式遙測資料

前面的 lab 主要觀察 VM、Apache、Ops Agent 和網路流量。這些資料大多來自基礎設施或作業系統。

OpenTelemetry 則是讓應用程式自己產生遙測資料的標準。常見資料包含：

- Traces：一次請求經過哪些步驟、花了多少時間
- Metrics：應用程式自訂的計數、延遲、佇列長度等數值
- Logs：應用程式事件與錯誤訊息

在這個延伸練習中，會執行一個 Python 範例程式，產生 traces 和 metrics。接著使用 VM 上的 Ops Agent OTLP receiver 收資料，送到 Cloud Monitoring 和 Cloud Trace。

相關文件：

- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Collect OpenTelemetry Protocol metrics and traces with the Ops Agent](https://cloud.google.com/monitoring/agent/ops-agent/otlp)

### 步驟 1：先在 Cloud Shell 看 console exporter

先在 Cloud Shell 執行範例，觀察 OpenTelemetry 產生的資料長什麼樣子：

```bash
cd samples/opentelemetry
uv sync
uv run python otel_demo.py --exporter console --iterations 3
cd ../..
```

你會看到程式輸出 span 和 metric。這些資料還沒有送到 Google Cloud，只是印在 Cloud Shell 裡。

觀察重點：

- `service.name` 是 `gsp089-otel-demo`
- `handle_request` 是主要 span
- `render_response` 是巢狀 span
- `gsp089.demo.requests` 是請求數 counter
- `gsp089.demo.latency` 是延遲 histogram

### 步驟 2：啟用 Cloud Trace API

Ops Agent 會把 metrics 送到 Cloud Monitoring，把 traces 送到 Cloud Trace。啟用 Cloud Trace API：

```bash
gcloud services enable cloudtrace.googleapis.com
```

### 步驟 3：設定 Ops Agent 接收 OTLP

把範例設定檔複製到 VM：

```bash
gcloud compute scp \
  samples/opentelemetry/ops-agent-otlp-config.yaml \
  lamp-1-vm:/tmp/ops-agent-otlp-config.yaml \
  --zone "$(gcloud config get-value compute/zone)"
```

套用 Ops Agent 設定並重啟 agent：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "sudo cp /etc/google-cloud-ops-agent/config.yaml /tmp/google-cloud-ops-agent-config.yaml.backup 2>/dev/null || true; sudo cp /tmp/ops-agent-otlp-config.yaml /etc/google-cloud-ops-agent/config.yaml; sudo systemctl restart google-cloud-ops-agent; sudo systemctl status 'google-cloud-ops-agent*' --no-pager"
```

這個設定會讓 Ops Agent 在 VM 上接收 OTLP gRPC 資料。預設 endpoint 是：

```text
localhost:4317
```

### 步驟 4：把範例程式複製到 VM

先確認 VM 上有 `uv`：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command 'command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh'
```

接著建立範例目錄並複製程式：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "mkdir -p ~/otel-demo"

gcloud compute scp \
  samples/opentelemetry/otel_demo.py \
  samples/opentelemetry/pyproject.toml \
  samples/opentelemetry/uv.lock \
  lamp-1-vm:~/otel-demo/ \
  --zone "$(gcloud config get-value compute/zone)"
```

### 步驟 5：在 VM 上執行範例程式

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command 'cd ~/otel-demo && UV_BIN="$(command -v uv || echo ~/.local/bin/uv)" && "$UV_BIN" run python otel_demo.py --exporter otlp --endpoint localhost:4317 --iterations 10'
```

這次程式不會只把資料印在畫面上，而是會透過 OTLP 送到 VM 上的 Ops Agent。

### 步驟 6：在 Cloud Monitoring 查看自訂 metrics

等待 1 到 3 分鐘後，到 Console：

```text
Navigation menu > Monitoring > Metrics Explorer
```

搜尋下列 metric：

```text
workload.googleapis.com/gsp089.demo.requests
workload.googleapis.com/gsp089.demo.latency
```

也可以用 Cloud Shell 呼叫 Cloud Monitoring API，確認 metric descriptor 是否已建立：

```bash
PROJECT_ID="$(gcloud config get-value project)"

curl -s -G \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://monitoring.googleapis.com/v3/projects/${PROJECT_ID}/metricDescriptors" \
  --data-urlencode 'filter=metric.type = starts_with("workload.googleapis.com/gsp089.demo")' \
  | python3 -m json.tool
```

### 步驟 7：在 Cloud Trace 查看 traces

到 Console：

```text
Navigation menu > Trace > Trace Explorer
```

搜尋或篩選 service：

```text
gsp089-otel-demo
```

點進任一 trace，可以看到 `handle_request` 和 `render_response` 的父子關係，以及每個 span 的耗時。

### 這個延伸練習要理解的重點

- Ops Agent 負責收集 VM 系統層級資料，也可以接收應用程式送出的 OTLP 資料。
- OpenTelemetry 讓應用程式用標準格式描述 traces 和 metrics，不需要在程式裡直接呼叫 Cloud Monitoring API 或 Cloud Trace API。
- Terraform 建立的是基礎設施；OpenTelemetry 補上的是應用程式行為的可觀測性。
- 後續可以把自訂 metric 放進 dashboard，或針對應用程式延遲建立 alert policy。

## 清理資源

lab 結束前可以刪除 Terraform 建立的資源：

```bash
terraform destroy
```

Terraform 會列出即將刪除的資源。確認內容後輸入 `yes`。

如果有設定 `alert_email`，清理資源後也可以避免 lab 資源尚未回收期間繼續寄送通知。

## Terraform 檔案對照

- `versions.tf`：Terraform 與 Google provider 設定
- `variables.tf`：輸入變數，例如 project、region、zone
- `main.tf`：VM、防火牆、startup script
- `monitoring.tf`：uptime check、alert policy、notification channel、dashboard
- `outputs.tf`：輸出 Apache URL、VM 外部 IP 等資訊
- `samples/opentelemetry/`：OpenTelemetry 延伸練習範例
- `terraform.tfvars.example`：變數檔範例

## 常見問題

### `terraform apply` 套用到錯誤 project

確認目前 gcloud project 和 `terraform.tfvars`：

```bash
gcloud config list project
cat terraform.tfvars
```

`project_id` 必須是本次 lab 提供的 Google Cloud project。

### Apache URL 打不開

startup script 需要時間安裝套件。先等待 1 到 3 分鐘，再檢查：

```bash
terraform output apache_url
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "sudo systemctl status apache2 --no-pager"
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command "sudo tail -n 80 /var/log/gsp089-startup.log"
```

### Monitoring 圖表沒有資料

Ops Agent 指標需要幾分鐘才會送到 Cloud Monitoring。確認 agent 狀態：

```bash
gcloud compute ssh lamp-1-vm \
  --zone "$(gcloud config get-value compute/zone)" \
  --command 'sudo systemctl status "google-cloud-ops-agent*"'
```

### VM 建立失敗：zone 沒有足夠資源

如果 `terraform apply` 顯示類似訊息：

```text
The zone ... does not have enough resources available to fulfill the request.
A e2-medium VM instance is currently unavailable ...
```

代表 lab 指定的 zone 暫時沒有足夠容量建立 VM。不要任意改 region、zone 或 machine type，否則可能導致 Skills Boost progress check 無法通過。

這是 Compute Engine 的資源可用性錯誤。可參考 Google Cloud 官方文件：[排解資源可用性錯誤](https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-resource-availability?hl=zh-tw)。

先等待幾分鐘，然後在相同設定下再次執行：

```bash
terraform apply
```

如果多次重試仍失敗，請保留 lab 指定的設定，重新啟動 lab 或稍後再試。
