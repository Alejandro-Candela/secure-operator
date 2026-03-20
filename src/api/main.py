"""
Secure Operator — FastAPI Application Entrypoint
Provides REST endpoints for the sandboxed agentic pipeline.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config.settings import get_settings
from src.utils.logging import get_logger, setup_telemetry

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    logger.info(
        "Starting Secure Operator API",
        extra={
            "environment": settings.environment,
            "deployment_mode": settings.deployment_mode,
            "sandbox_enabled": settings.module_sandbox,
        },
    )
    if settings.module_observability:
        setup_telemetry(settings)
    yield
    logger.info("Shutting down Secure Operator API")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="Secure Operator API",
        description="Sandboxed agentic pipeline with NVIDIA NeMo-Claw guardrails. "
        f"Mode: {settings.deployment_mode}",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
        return response

    from src.api.routers import agent, health
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])

    return app


class ChatRequest(BaseModel):
    """Incoming chat request payload."""
    message: str
    thread_id: str | None = None
    sandbox_enabled: bool = True


class ChatResponse(BaseModel):
    """Chat response payload."""
    message: str
    thread_id: str
    sandbox_execution_log: list[dict] = []
    trace_id: str | None = None


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.log_level.lower(),
        reload=(settings.environment == "development"),
    )
