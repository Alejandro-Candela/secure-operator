"""
Secure Operator — Structured Logging with OpenTelemetry
Provides JSON-structured logging correlated with OTel trace IDs.
"""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from pythonjsonlogger import jsonlogger

if TYPE_CHECKING:
    from src.config.settings import AppSettings


class OTelJsonFormatter(jsonlogger.JsonFormatter):
    """JSON log formatter that injects OTel trace and span IDs when available."""

    def add_fields(
        self,
        log_record: dict,
        record: logging.LogRecord,
        message_dict: dict,
    ) -> None:
        """Append OTel context fields to every log record."""
        super().add_fields(log_record, record, message_dict)
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                log_record["trace_id"] = format(ctx.trace_id, "032x")
                log_record["span_id"] = format(ctx.span_id, "016x")
        except ImportError:
            pass  # OTel not installed — skip trace correlation
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


def get_logger(name: str) -> logging.Logger:
    """Return a structured JSON logger for the given module name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            OTelJsonFormatter(
                "%(asctime)s %(level)s %(logger)s %(message)s"
            )
        )
        logger.addHandler(handler)
    return logger


def setup_telemetry(settings: "AppSettings") -> None:
    """
    Initialise OpenTelemetry SDK and auto-instrumentation.
    Only runs if modules.observability is true.
    """
    if not settings.module_observability:
        logging.getLogger(__name__).info("Observability module disabled — skipping OTel setup")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logging.getLogger(__name__).warning(
            "OTel packages not installed. Install with: uv sync (production deps)"
        )
        return

    resource = Resource(attributes={SERVICE_NAME: "secure-operator"})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=settings.environment != "production",
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    logging.getLogger(__name__).info(
        "OpenTelemetry initialised",
        extra={"service": "secure-operator"},
    )
