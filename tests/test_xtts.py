"""Tests for the XTTS voice-clone speaker and speaker factory (subprocess mocked)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from mourice.config import Settings
from mourice.voice import Speaker, XttsDaemonSpeaker, XttsSpeaker, build_speaker
from mourice.voice import audio as audio_module


def test_save_builds_command() -> None:
    captured: list[Sequence[str]] = []
    speaker = XttsSpeaker(
        "py.exe",
        "scripts/xtts_speak.py",
        "ref.wav",
        language="ru",
        device="cpu",
        runner=captured.append,
    )
    speaker.save("привет", "out.wav")

    cmd = list(captured[0])
    assert cmd[0] == "py.exe"
    assert "scripts/xtts_speak.py" in cmd[1]
    assert "--text" in cmd and "привет" in cmd
    assert "--speaker" in cmd and "ref.wav" in cmd
    assert "--language" in cmd and "ru" in cmd
    assert "--device" in cmd and "cpu" in cmd


def test_say_runs_and_plays(monkeypatch: pytest.MonkeyPatch) -> None:
    played: list[Any] = []
    monkeypatch.setattr(audio_module, "play_wav", lambda p: played.append(p))
    calls: list[Sequence[str]] = []
    speaker = XttsSpeaker("py", "s.py", "ref.wav", runner=calls.append)

    speaker.say("йо")
    assert len(calls) == 1
    assert len(played) == 1


def test_say_empty_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    played: list[Any] = []
    monkeypatch.setattr(audio_module, "play_wav", lambda p: played.append(p))
    calls: list[Sequence[str]] = []
    XttsSpeaker("py", "s.py", "ref.wav", runner=calls.append).say("   ")
    assert calls == []
    assert played == []


def test_factory_piper() -> None:
    settings = Settings(_env_file=None, tts_engine="piper", piper_voice="v.onnx")  # type: ignore[call-arg]
    assert isinstance(build_speaker(settings), Speaker)


def test_factory_xtts(monkeypatch: pytest.MonkeyPatch) -> None:
    """build_speaker with xtts engine should start the daemon and return XttsDaemonSpeaker."""
    import subprocess

    fake_proc = type("P", (), {
        "poll": lambda self: None,
        "stdout": __import__("io").StringIO("[xtts_daemon] Ready on port 5199\n"),
        "stderr": __import__("io").StringIO(""),
        "terminate": lambda self: None,
    })()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: fake_proc)

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        tts_engine="xtts",
        xtts_python="py.exe",
        speaker_reference="ref.wav",
    )
    assert isinstance(build_speaker(settings), XttsDaemonSpeaker)


def test_factory_piper_missing_voice() -> None:
    settings = Settings(_env_file=None, tts_engine="piper", piper_voice="")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="MOURICE_PIPER_VOICE"):
        build_speaker(settings)


def test_factory_xtts_missing_config() -> None:
    settings = Settings(_env_file=None, tts_engine="xtts")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="MOURICE_XTTS_PYTHON"):
        build_speaker(settings)
