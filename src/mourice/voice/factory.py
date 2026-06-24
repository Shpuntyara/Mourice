"""Build the configured TTS speaker (Piper or XTTS voice clone)."""

from __future__ import annotations

from typing import Protocol

from mourice.config import Settings

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
        return XttsSpeaker(
            settings.xtts_python,
            settings.xtts_script,
            settings.speaker_reference,
            language=settings.voice_language,
            device=settings.xtts_device,
        )

    if not settings.piper_voice:
        raise ValueError("Set MOURICE_PIPER_VOICE to a Piper .onnx voice file.")
    return Speaker(settings.piper_voice)
