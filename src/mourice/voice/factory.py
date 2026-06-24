"""Build the configured TTS speaker (Piper or XTTS voice clone)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from mourice.config import Settings

# Repo root (two levels above this file: src/mourice/voice/factory.py → repo root)
_REPO_ROOT = Path(__file__).parent.parent.parent.parent

from .tts import Speaker
from .xtts import XttsSpeaker

__all__ = ["VoiceSpeaker", "build_speaker"]


class VoiceSpeaker(Protocol):
    """Anything that can speak text aloud."""

    def say(self, text: str) -> None: ...


def build_speaker(settings: Settings) -> VoiceSpeaker:
    """Return the speaker for the configured ``tts_engine``.

    Raises ValueError if the chosen engine is misconfigured.
    """
    if settings.tts_engine == "xtts":
        if not settings.speaker_reference or not settings.xtts_python:
            raise ValueError(
                "Set MOURICE_XTTS_PYTHON and MOURICE_SPEAKER_REFERENCE for the xtts engine."
            )
        script = Path(settings.xtts_script)
        if not script.is_absolute():
            script = _REPO_ROOT / script
        return XttsSpeaker(
            settings.xtts_python,
            script,
            settings.speaker_reference,
            language=settings.voice_language,
            device=settings.xtts_device,
        )

    if not settings.piper_voice:
        raise ValueError("Set MOURICE_PIPER_VOICE to a Piper .onnx voice file.")
    return Speaker(settings.piper_voice)
