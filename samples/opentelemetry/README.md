# OpenTelemetry 範例

這個範例會產生少量 traces 和 metrics。可以先把遙測資料印在 console，也可以透過 OTLP 匯出到 Ops Agent receiver。

程式會重複產生幾個固定教學情境：

- `/`：正常且快速的首頁請求。
- `/api/status`：有後端檢查步驟的中等延遲請求。
- `/checkout`：較慢的結帳請求。
- `/checkout` status `500`：模擬 inventory timeout 的錯誤請求。

span 可以先理解成「一次請求中的一段工作」。多個有父子關係的 span 組合起來，就是一筆 trace。

觀察時請比較 request counter、error counter、latency histogram，以及 Cloud Trace 裡 `handle_request` 和子 span 的耗時差異。

在 Cloud Trace 找特定路徑時，使用 Trace Explorer 的 `Add filter` > `Add attribute filter`，Key 輸入 `http.route`，Value 輸入 `/`、`/api/status` 或 `/checkout`。錯誤 trace 可以再加 `http.response.status_code = 500`。

在本機用 console output 執行：

```bash
uv sync
uv run python otel_demo.py --exporter console --iterations 3
```

在已設定 OTLP receiver 的 VM 上執行：

```bash
uv run python otel_demo.py --exporter otlp --endpoint localhost:4317 --iterations 10
```
