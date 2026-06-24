"""XTTS voice-clone speaker (subprocess to the isolated env).

Mourice's core env stays clean; the heavy coqui/torch stack lives in a separate
venv. This backend shells out to ``scripts/xtts_speak.py`` to synthesize a WAV
with the cloned voice, then plays it. Same surface as ``Speaker``.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from mourice.log import logger

from . import audio

__all__ = ["XttsSpeaker"]

Runner = Callable[[Sequence[str]], None]


def _default_runner(cmd: Sequence[str]) -> None:
    subprocess.run(list(cmd), check=True, capture_output=True)


class XttsSpeaker:
    """Speaks text using an XTTS voice clone via the isolated env subprocess."""

    def __init__(
        self,
        python_exe: str | Path,
        script: str | Path,
        speaker_reference: str | Path,
        *,
        language: str = "ru",
        device: str = "cpu",
        runner: Runner | None = None,
    ) -> None:
        self._python = str(python_exe)
        self._script = str(script)
        self._reference = str(speaker_reference)
        self._language = language
        self._device = device
        self._run: Runner = runner or _default_runner

    def save(self, text: str, path: str | Path) -> None:
        """Synthesize text to a WAV file at ``path`` using the clone."""
        cmd = [
            self._python,
            self._script,
            "--text",
            text,
            "--speaker",
            self._reference,
            "--out",
            str(path),
            "--language",
            self._language,
            "--device",
            self._device,
        ]
        logger.bind(device=self._device).debug("XTTS synth")
        self._run(cmd)

    def say(self, text: str) -> None:
        """Synthesize and play text aloud with the cloned voice."""
        if not text.strip():
            return
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "reply.wav"
            self.save(text, out)
            audio.play_wav(out)
