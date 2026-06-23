"""Tests for CLI command dispatch (mocked side effects)."""

from __future__ import annotations

import sys
from typing import Any

import pytest

from mourice import cli
from mourice.config import Settings


@pytest.fixture(autouse=True)
def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: Settings(_env_file=None))  # type: ignore[call-arg]
    monkeypatch.setattr(cli, "setup_logging", lambda settings: None)


def test_main_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, Any] = {}
    monkeypatch.setattr(cli, "_banner", lambda settings: called.setdefault("banner", True))
    monkeypatch.setattr(sys, "argv", ["mourice"])
    cli.main()
    assert called.get("banner")


def test_main_sync_with_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(cli, "_run_sync", lambda settings, *, reset: captured.update(reset=reset))
    monkeypatch.setattr(sys, "argv", ["mourice", "sync", "--reset"])
    cli.main()
    assert captured["reset"] is True


def test_main_eval(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, Any] = {}
    monkeypatch.setattr(cli, "_run_eval", lambda settings: called.setdefault("eval", True))
    monkeypatch.setattr(sys, "argv", ["mourice", "eval"])
    cli.main()
    assert called.get("eval")


def test_main_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    import mourice.interfaces as interfaces

    called: dict[str, Any] = {}
    monkeypatch.setattr(interfaces, "run_chat", lambda settings: called.setdefault("chat", True))
    monkeypatch.setattr(sys, "argv", ["mourice", "chat"])
    cli.main()
    assert called.get("chat")
