"""Tests for voice audio I/O (sounddevice mocked — no hardware needed)."""

from __future__ import annotations

import sys
import types
from typing import Any

import numpy as np
import pytest

from mourice.voice import audio


def _install_fake_sd(monkeypatch: pytest.MonkeyPatch, calls: dict[str, Any]) -> None:
    module = types.ModuleType("sounddevice")

    class _Stream:
        def __init__(self, **_: Any) -> None: ...
        def __enter__(self) -> _Stream:
            return self

        def __exit__(self, *_: Any) -> None:
            return None

    module.InputStream = lambda **kw: _Stream()  # type: ignore[attr-defined]
    module.sleep = lambda ms: None  # type: ignore[attr-defined]
    module.play = lambda samples, samplerate: calls.update(  # type: ignore[attr-defined]
        played=len(samples), rate=samplerate
    )
    module.wait = lambda: calls.update(waited=True)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sounddevice", module)


def test_record_returns_array_and_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_sd(monkeypatch, {})
    result = audio.record_until_enter(wait_for_enter=lambda: None)
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.int16  # empty (no frames from fake stream)


def test_play_calls_sounddevice(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, Any] = {}
    _install_fake_sd(monkeypatch, calls)
    audio.play(np.zeros(1600, dtype=np.int16), sample_rate=16000)
    assert calls["played"] == 1600
    assert calls["rate"] == 16000
    assert calls["waited"] is True


def test_play_wav(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    import wave

    path = tmp_path / "a.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(np.zeros(800, dtype=np.int16).tobytes())

    calls: dict[str, Any] = {}
    _install_fake_sd(monkeypatch, calls)
    audio.play_wav(path)
    assert calls["played"] == 800
