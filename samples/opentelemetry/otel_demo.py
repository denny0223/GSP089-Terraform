#!/usr/bin/env python3
import argparse
import random
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
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


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
    latency_histogram = meter.create_histogram(
        "gsp089.demo.latency",
        unit="ms",
        description="Synthetic request latency.",
    )

    routes = ["/", "/checkout", "/api/status"]

    for index in range(args.iterations):
        route = random.choice(routes)
        latency_ms = random.randint(40, 350)

        with tracer.start_as_current_span("handle_request") as span:
            span.set_attribute("http.request.method", "GET")
            span.set_attribute("url.path", route)
            span.set_attribute("demo.iteration", index + 1)
            time.sleep(latency_ms / 1000)

            with tracer.start_as_current_span("render_response") as child_span:
                child_span.set_attribute("demo.template", "apache-default")
                time.sleep(random.randint(10, 80) / 1000)

        attributes = {"route": route}
        request_counter.add(1, attributes=attributes)
        latency_histogram.record(latency_ms, attributes=attributes)
        print(f"emitted request {index + 1}: route={route} latency_ms={latency_ms}")

    trace_provider.shutdown()
    meter_provider.shutdown()


if __name__ == "__main__":
    main()
