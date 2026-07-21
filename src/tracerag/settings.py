"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for TraceRAG.

    Values are read from environment variables prefixed with ``TRACERAG_`` and
    optionally from a local ``.env`` file (never committed).
    """

    model_config = SettingsConfigDict(
        env_prefix="TRACERAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model_name: str = Field(
        default="local-openai-compatible-model",
        description="Model name for the local OpenAI-compatible endpoint.",
    )
    base_url: str = Field(
        default="http://localhost:11434/v1",
        description="Base URL of the OpenAI-compatible model endpoint.",
    )
    api_key: str = Field(
        default="ollama",
        description="API key for the local model endpoint.",
    )
    docs_path: Path = Field(
        default=Path("data/docs"),
        description="Directory containing the Markdown SOP corpus.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level for the application.",
    )

    @property
    def docs_path_resolved(self) -> Path:
        """Resolve the corpus path relative to the process CWD."""
        return self.docs_path.resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide cached :class:`Settings` instance."""
    return Settings()