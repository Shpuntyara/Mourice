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

    # Voice (Phase 2)
    whisper_model: str = "small"  # faster-whisper model size
    voice_language: str = "ru"
    tts_engine: str = "piper"  # "piper" | "xtts"
    piper_voice: str = ""  # path to a Piper .onnx voice model
    # XTTS voice-clone (isolated env, called as a subprocess)
    xtts_python: str = ""  # path to .venv-xtts python
    xtts_script: str = "scripts/xtts_speak.py"
    speaker_reference: str = ""  # reference voice .wav to clone
    xtts_device: str = "cpu"  # "cpu" | "cuda"

    # Runtime
    log_level: str = Field(default="INFO")


def get_settings() -> Settings:
    """Return the application settings (instantiates from environment)."""
    return Settings()
