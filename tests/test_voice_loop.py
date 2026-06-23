"""Tests for the voice interface loop (all I/O mocked)."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from mourice.config import Settings
from mourice.core import Orchestrator
from mourice.interfaces.voice import run_voice
from mourice.voice import Speaker, Transcriber


class _FakeConsole:
    def __init__(self, inputs: list[str]) -> None:
        self._inputs = inputs
        self.printed: list[str] = []

    def input(self, prompt: str = "") -> str:
        return self._inputs.pop(0)

    def print(self, *args: Any, **kwargs: Any) -> None:
        self.printed.append(" ".join(str(a) for a in args))


class _FakeOrch:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.seen: list[str] = []

    def run(self, user_input: str) -> str:
        self.seen.append(user_input)
        return self._reply


class _FakeTranscriber:
    def __init__(self, text: str) -> None:
        self._text = text

    def transcribe(self, samples: Any, *, sample_rate: int = 16000) -> str:
        return self._text


class _FakeSpeaker:
    def __init__(self) -> None:
        self.said: list[str] = []

    def say(self, text: str) -> None:
        self.said.append(text)


def _settings() -> Settings:
    return Settings(_env_file=None, piper_voice="x.onnx")  # type: ignore[call-arg]


def test_one_turn_then_quit() -> None:
    console = _FakeConsole(["", "q"])
    orch = _FakeOrch("Готово, бро.")
    speaker = _FakeSpeaker()

    run_voice(
        _settings(),
        console=cast(Any, console),
        orchestrator=cast(Orchestrator, orch),
        transcriber=cast(Transcriber, _FakeTranscriber("какой план?")),
        speaker=cast(Speaker, speaker),
        recorder=lambda: np.zeros(10, dtype=np.int16),
    )

    assert orch.seen == ["какой план?"]
    assert speaker.said == ["Готово, бро."]


def test_empty_transcription_skips() -> None:
    console = _FakeConsole(["", "q"])
    orch = _FakeOrch("nope")
    speaker = _FakeSpeaker()

    run_voice(
        _settings(),
        console=cast(Any, console),
        orchestrator=cast(Orchestrator, orch),
        transcriber=cast(Transcriber, _FakeTranscriber("")),
        speaker=cast(Speaker, speaker),
        recorder=lambda: np.zeros(10, dtype=np.int16),
    )

    assert orch.seen == []  # nothing transcribed -> no orchestrator call
    assert speaker.said == []


def test_missing_voice_aborts() -> None:
    console = _FakeConsole([])
    settings = Settings(_env_file=None, piper_voice="")  # type: ignore[call-arg]
    run_voice(settings, console=cast(Any, console))
    assert any("MOURICE_PIPER_VOICE" in line for line in console.printed)
