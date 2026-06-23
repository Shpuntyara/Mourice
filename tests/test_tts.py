"""Tests for text-to-speech (Piper voice mocked)."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from mourice.voice import Speaker
from mourice.voice import audio as audio_module


class _FakeVoice:
    """Writes a tiny silent WAV, mimicking PiperVoice.synthesize_wav."""

    def __init__(self, n_samples: int = 1600, rate: int = 22050) -> None:
        self._n = n_samples
        self._rate = rate
        self.said: list[str] = []

    def synthesize_wav(self, text: str, wav: wave.Wave_write) -> None:
        self.said.append(text)
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(self._rate)
        wav.writeframes(np.zeros(self._n, dtype=np.int16).tobytes())


def test_synthesize_returns_samples() -> None:
    speaker = Speaker("unused.onnx", voice=_FakeVoice(n_samples=2000, rate=22050))
    samples, rate = speaker.synthesize("привет")
    assert len(samples) == 2000
    assert rate == 22050


def test_say_plays_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    played: dict[str, Any] = {}
    monkeypatch.setattr(audio_module, "play", lambda s, r: played.update(n=len(s), rate=r))
    speaker = Speaker("unused.onnx", voice=_FakeVoice(n_samples=800))
    speaker.say("скажи это")
    assert played["n"] == 800


def test_say_empty_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    played: dict[str, Any] = {}
    monkeypatch.setattr(audio_module, "play", lambda s, r: played.update(called=True))
    Speaker("x.onnx", voice=_FakeVoice()).say("   ")
    assert played == {}


def test_save_writes_wav(tmp_path: Path) -> None:
    out = tmp_path / "out.wav"
    Speaker("x.onnx", voice=_FakeVoice(n_samples=1200)).save("текст", out)
    assert out.exists()
    with wave.open(str(out), "rb") as w:
        assert w.getnframes() == 1200
