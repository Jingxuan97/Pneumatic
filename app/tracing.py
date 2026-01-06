# app/tracing.py
"""
OpenTelemetry tracing configuration.
"""
import os
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def setup_tracing(app, engine=None):
    """
    Setup OpenTelemetry tracing.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine (optional, for SQL instrumentation)
    """
    # Skip tracing setup during tests to avoid I/O errors with closed file handles
    if "pytest" in sys.modules or os.environ.get("DISABLE_TRACING") == "1":
        return trace.get_tracer(__name__)

    try:
        # Create resource with service name
        resource = Resource.create({
            "service.name": "pneumatic-chat",
            "service.version": "1.0.0",
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        # Add console exporter (in production, use OTLP exporter)
        console_exporter = ConsoleSpanExporter()
        span_processor = BatchSpanProcessor(console_exporter)
        provider.add_span_processor(span_processor)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        # If tracing setup fails (e.g., during test teardown), continue without it
        pass

    return trace.get_tracer(__name__)
