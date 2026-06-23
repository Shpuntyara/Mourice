"""Test the application wiring factory."""

from __future__ import annotations

from pathlib import Path

from mourice.app import build_orchestrator
from mourice.config import Settings
from mourice.core import Orchestrator


def test_build_orchestrator(tmp_path: Path) -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        obsidian_vault=str(tmp_path / "vault"),
        chroma_dir=str(tmp_path / "chroma"),
    )
    orchestrator = build_orchestrator(settings)
    assert isinstance(orchestrator, Orchestrator)
    assert orchestrator.history == []
