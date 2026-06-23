"""Tests for speech-to-text (Whisper model mocked)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from mourice.voice import Transcriber


@dataclass
class _Segment:
    text: str


class _FakeModel:
    def __init__(self, segments: list[_Segment]) -> None:
        self._segments = segments
        self.calls: list[dict[str, Any]] = []

    def transcribe(
        self, audio: Any, language: str | None = None
    ) -> tuple[list[_Segment], dict[str, Any]]:
        self.calls.append({"language": language, "max": float(audio.max()) if audio.size else 0.0})
        return self._segments, {}


def test_transcribe_joins_segments() -> None:
    model = _FakeModel([_Segment(" Привет"), _Segment("мир ")])
    t = Transcriber(model=model, language="ru")
    samples = np.array([1000, -2000, 3000], dtype=np.int16)
    assert t.transcribe(samples) == "Привет мир"
    assert model.calls[0]["language"] == "ru"


def test_empty_audio_returns_empty() -> None:
    model = _FakeModel([_Segment("should not run")])
    t = Transcriber(model=model)
    assert t.transcribe(np.zeros(0, dtype=np.int16)) == ""
    assert model.calls == []  # model not called


def test_int16_normalised_to_float() -> None:
    model = _FakeModel([_Segment("x")])
    t = Transcriber(model=model)
    t.transcribe(np.array([32767], dtype=np.int16))
    assert model.calls[0]["max"] <= 1.0  # normalised to [-1, 1]
