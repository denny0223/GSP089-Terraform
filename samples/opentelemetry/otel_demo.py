#!/usr/bin/env python3
import argparse
import time

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

SCENARIOS = [
    {
        "name": "fast-homepage",
        "route": "/",
        "status_code": 200,
        "steps": [
            ("load_config", 12, None),
            ("render_response", 28, None),
        ],
    },
    {
        "name": "healthy-status-api",
        "route": "/api/status",
        "status_code": 200,
        "steps": [
            ("check_cache", 35, None),
            ("query_health_backend", 95, None),
            ("render_response", 18, None),
        ],
    },
    {
        "name": "slow-checkout",
        "route": "/checkout",
        "status_code": 200,
        "steps": [
            ("load_user", 55, None),
            ("query_inventory", 190, None),
            ("prepare_payment", 85, None),
            ("render_response", 35, None),
        ],
    },
    {
        "name": "checkout-inventory-error",
        "route": "/checkout",
        "status_code": 500,
        "error_type": "inventory_timeout",
        "steps": [
            ("load_user", 50, None),
            ("query_inventory", 260, "inventory_timeout"),
            ("render_error_page", 30, None),
        ],
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Emit demo OpenTelemetry traces and metrics."
    )
    parser.add_argument(
        "--exporter",
        choices=["console", "otlp"],
        default="console",
        help="Where to export telemetry.",
    )
    parser.add_argument(
        "--endpoint",
        default="localhost:4317",
        help="OTLP gRPC endpoint used when --exporter otlp is selected.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of synthetic requests to emit.",
    )
    return parser.parse_args()


def configure_telemetry(exporter, endpoint):
    resource = Resource.create(
        {
            "service.name": "gsp089-otel-demo",
            "service.version": "1.0.0",
            "deployment.environment": "skills-boost-lab",
        }
    )

    trace_provider = TracerProvider(resource=resource)
    if exporter == "otlp":
        span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    else:
        span_exporter = ConsoleSpanExporter()
        metric_exporter = ConsoleMetricExporter()

    trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=1000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    return trace_provider, meter_provider


def main():
    args = parse_args()
    trace_provider, meter_provider = configure_telemetry(args.exporter, args.endpoint)

    tracer = trace.get_tracer("gsp089.otel.demo")
    meter = metrics.get_meter("gsp089.otel.demo")

    request_counter = meter.create_counter(
        "gsp089.demo.requests",
        unit="1",
        description="Number of synthetic requests processed by the demo app.",
    )
    error_counter = meter.create_counter(
        "gsp089.demo.errors",
        unit="1",
        description="Number of synthetic failed requests emitted by the demo app.",
    )
    latency_histogram = meter.create_histogram(
        "gsp089.demo.latency",
        unit="ms",
        description="Synthetic request latency.",
    )

    for index in range(args.iterations):
        scenario = SCENARIOS[index % len(SCENARIOS)]
        route = scenario["route"]
        status_code = scenario["status_code"]
        latency_ms = sum(step_duration for _, step_duration, _ in scenario["steps"])

        with tracer.start_as_current_span("handle_request") as span:
            span.set_attribute("http.request.method", "GET")
            span.set_attribute("http.route", route)
            span.set_attribute("http.response.status_code", status_code)
            span.set_attribute("url.path", route)
            span.set_attribute("demo.iteration", index + 1)
            span.set_attribute("demo.scenario", scenario["name"])
            span.set_attribute("demo.latency_ms", latency_ms)

            if status_code != 200:
                error_type = scenario.get("error_type", "application_error")
                span.set_attribute("error.type", error_type)
                span.set_status(Status(StatusCode.ERROR, error_type))

            for step_name, step_duration_ms, step_error in scenario["steps"]:
                with tracer.start_as_current_span(step_name) as child_span:
                    child_span.set_attribute("demo.step", step_name)
                    child_span.set_attribute("demo.step_duration_ms", step_duration_ms)
                    time.sleep(step_duration_ms / 1000)

                    if step_error:
                        exception = RuntimeError(step_error)
                        child_span.set_attribute("error.type", step_error)
                        child_span.record_exception(exception)
                        child_span.set_status(Status(StatusCode.ERROR, step_error))
                        span.record_exception(exception)

        attributes = {
            "route": route,
            "status_code": str(status_code),
            "scenario": scenario["name"],
        }
        request_counter.add(1, attributes=attributes)
        latency_histogram.record(latency_ms, attributes=attributes)
        if status_code != 200:
            error_counter.add(1, attributes=attributes)

        print(
            "emitted request "
            f"{index + 1}: scenario={scenario['name']} route={route} "
            f"status={status_code} latency_ms={latency_ms}"
        )

    trace_provider.shutdown()
    meter_provider.shutdown()


if __name__ == "__main__":
    main()
