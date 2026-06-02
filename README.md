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
