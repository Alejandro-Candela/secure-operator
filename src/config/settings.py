"""
Secure Operator — Pydantic Settings
Loads config from environment variables and config.yaml.
Supports deployment_mode: poc | production with module toggles.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InferenceSettings(BaseSettings):
    """Inference engine configuration."""

    provider: Literal["ollama", "vllm", "azure_ai_foundry", "nvidia-nemotron"] = "ollama"
    base_url: str = "http://localhost:11434"
    api_key: SecretStr = Field(default=SecretStr(""))
    model: str = "qwen3:4b"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    timeout_seconds: int = Field(default=120, gt=0)

    model_config = SettingsConfigDict(env_prefix="VLLM_")


class SandboxSettings(BaseSettings):
    """OpenShell / Docker sandbox configuration."""

    runtime: Literal["nvidia-openshell", "docker-subprocess"] = "docker-subprocess"
    openshell_enabled: bool = False
    max_memory_mb: int = 512
    max_cpu_cores: int = 1
    max_execution_time_seconds: int = 30
    network_policy: Literal["isolated", "restricted", "full"] = "isolated"

    model_config = SettingsConfigDict(env_prefix="OPENSHELL_")


class SecuritySettings(BaseSettings):
    """NeMo-Claw guardrails configuration."""

    nemoclaw_enabled: bool = False
    nemoclaw_policy_path: str = "./config/nemoclaw_policy.yaml"
    nemoclaw_privacy_mode: Literal["strict", "balanced", "permissive"] = "strict"
    nemoclaw_pii_redaction: bool = True
    nemoclaw_jailbreak_detection: bool = True
    nemo_guardrails_enabled: bool = False

    model_config = SettingsConfigDict(env_prefix="")


class ObservabilitySettings(BaseSettings):
    """OpenTelemetry observability configuration."""

    otel_enabled: bool = False
    otel_service_name: str = "secure-operator"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_exporter_otlp_protocol: str = "grpc"

    model_config = SettingsConfigDict(env_prefix="")


class AppSettings(BaseSettings):
    """Root application settings — loaded from .env."""

    project_name: str = "secure-operator"
    environment: Literal["development", "staging", "production"] = "development"
    deployment_mode: Literal["poc", "production"] = "poc"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Module toggles
    module_inference: bool = True
    module_vector_db: bool = True
    module_orchestration: bool = True
    module_sandbox: bool = False
    module_security: bool = False
    module_observability: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_workers: int = 4
    api_cors_origins: str = "http://localhost:3001"

    # Database
    database_url: SecretStr = Field(default=SecretStr("postgresql://postgres:postgres@localhost:5432/secure_operator_db"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("api_cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Convert comma-separated origins string to list."""
        return [origin.strip() for origin in v.split(",")]

    @property
    def cors_origins(self) -> list[str]:
        """Return parsed CORS origins."""
        return self.parse_cors_origins(self.api_cors_origins)

    @property
    def otel_enabled(self) -> bool:
        """OTel is only active if the observability module is enabled."""
        return self.module_observability


def load_yaml_config(path: Path = Path("config.yaml")) -> dict:
    """
    Load the config.yaml file.

    Raises:
        FileNotFoundError: If config.yaml does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at {path}. "
            "Run: cp config.yaml.example config.yaml"
        )
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached application settings."""
    return AppSettings()
