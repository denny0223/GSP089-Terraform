# OpenTelemetry 範例

這個範例會產生少量 traces 和 metrics。可以先把遙測資料印在 console，也可以透過 OTLP 匯出到 Ops Agent receiver。

在本機用 console output 執行：

```bash
uv sync
uv run python otel_demo.py --exporter console --iterations 3
```

在已設定 OTLP receiver 的 VM 上執行：

```bash
uv run python otel_demo.py --exporter otlp --endpoint localhost:4317 --iterations 10
```
