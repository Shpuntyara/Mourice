"""Tests for configuration loading."""

from __future__ import annotations

from mourice import __version__
from mourice.config import Settings, get_settings


def test_version_is_set() -> None:
    assert __version__


def test_settings_defaults(monkeypatch: object) -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.default_model
    assert settings.ollama_host.startswith("http")
    assert settings.chroma_collection == "mourice_memory"


def test_get_settings_returns_settings() -> None:
    assert isinstance(get_settings(), Settings)
