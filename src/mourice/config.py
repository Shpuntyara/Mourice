"""Application configuration loaded from environment / .env."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for Mourice.

    Values are read from environment variables prefixed with ``MOURICE_``
    (see ``.env.example``). Secrets must never be committed.
    """

    model_config = SettingsConfigDict(
        env_prefix="MOURICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (Ollama)
    ollama_host: str = "http://localhost:11434"
    default_model: str = "qwen2.5:14b"
    # Multilingual embedding model served by Ollama (strong on RU/PL).
    embedding_model: str = "bge-m3"

    # Knowledge base
    obsidian_vault: str = ""
    chroma_dir: str = ""
    chroma_collection: str = "mourice_memory"

    # Runtime
    log_level: str = Field(default="INFO")


def get_settings() -> Settings:
    """Return the application settings (instantiates from environment)."""
    return Settings()
