# app/tracing.py
"""
OpenTelemetry tracing configuration.
"""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def setup_tracing(app, engine=None):
    """
    Setup OpenTelemetry tracing.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine (optional, for SQL instrumentation)
    """
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

    # Instrument SQLAlchemy if engine provided
    if engine:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine if hasattr(engine, 'sync_engine') else engine)

    return trace.get_tracer(__name__)
