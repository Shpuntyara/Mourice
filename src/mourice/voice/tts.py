"""Text-to-speech via Piper (local, Russian voice).

Synthesizes to an in-memory WAV (version-independent) and plays it back.
Piper is imported lazily; the voice model is loaded on first use.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mourice.log import logger

from . import audio

if TYPE_CHECKING:
    import numpy as np

__all__ = ["Speaker"]


class Speaker:
    """Speaks text aloud using a Piper voice."""

    def __init__(self, voice_path: str | Path, *, voice: Any | None = None) -> None:
        self._voice_path = str(voice_path)
        self._voice = voice

    def _get_voice(self) -> Any:
        if self._voice is None:
            from piper import PiperVoice

            logger.bind(voice=self._voice_path).info("Loading Piper voice")
            self._voice = PiperVoice.load(self._voice_path)
        return self._voice

    def synthesize(self, text: str) -> tuple[np.ndarray[Any, Any], int]:
        """Synthesize text to (int16 samples, sample_rate)."""
        import numpy as np

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            self._get_voice().synthesize_wav(text, wav)
        buffer.seek(0)
        with wave.open(buffer, "rb") as wav:
            rate = wav.getframerate()
            frames = wav.readframes(wav.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)
        logger.bind(samples=len(samples), rate=rate).debug("Synthesized speech")
        return samples, rate

    def say(self, text: str) -> None:
        """Synthesize and play text aloud."""
        if not text.strip():
            return
        samples, rate = self.synthesize(text)
        audio.play(samples, rate)

    def save(self, text: str, path: str | Path) -> None:
        """Synthesize text to a WAV file."""
        with wave.open(str(path), "wb") as wav:
            self._get_voice().synthesize_wav(text, wav)
