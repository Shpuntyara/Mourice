"""Build the configured TTS speaker (Piper or XTTS voice clone)."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Protocol

from mourice.config import Settings
from mourice.log import logger

# Repo root: src/mourice/voice/factory.py → 4 levels up
_REPO_ROOT = Path(__file__).parent.parent.parent.parent

from .tts import Speaker
from .xtts import XttsDaemonSpeaker, XttsSpeaker

__all__ = ["VoiceSpeaker", "build_speaker"]

_DAEMON_STARTUP_TIMEOUT = 180  # seconds — model load on first run can take a while


class VoiceSpeaker(Protocol):
    """Anything that can speak text aloud."""

    def say(self, text: str) -> None: ...


def build_speaker(settings: Settings) -> VoiceSpeaker:
    """Return the speaker for the configured ``tts_engine``."""
    if settings.tts_engine == "xtts":
        if not settings.speaker_reference or not settings.xtts_python:
            raise ValueError(
                "Set MOURICE_XTTS_PYTHON and MOURICE_SPEAKER_REFERENCE for the xtts engine."
            )
        daemon_script = _REPO_ROOT / "scripts" / "xtts_daemon.py"
        cmd = [
            settings.xtts_python,
            str(daemon_script),
            "--speaker", settings.speaker_reference,
            "--language", settings.voice_language,
            "--device", settings.xtts_device,
            "--temperature", str(settings.xtts_temperature),
            "--speed", str(settings.xtts_speed),
            "--repetition-penalty", str(settings.xtts_repetition_penalty),
            "--top-k", str(settings.xtts_top_k),
            "--top-p", str(settings.xtts_top_p),
            "--pitch", str(settings.xtts_pitch),
            "--port", str(settings.xtts_daemon_port),
        ]
        logger.info("Starting XTTS daemon (model loading, please wait…)")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        deadline = time.time() + _DAEMON_STARTUP_TIMEOUT
        while time.time() < deadline:
            if proc.poll() is not None:
                stderr = proc.stderr.read() if proc.stderr else ""
                raise RuntimeError(f"XTTS daemon exited early:\n{stderr}")
            line = proc.stdout.readline() if proc.stdout else ""
            if "Ready" in line:
                logger.info("XTTS daemon ready")
                return XttsDaemonSpeaker(proc, port=settings.xtts_daemon_port)

        proc.terminate()
        raise RuntimeError("XTTS daemon did not become ready within timeout")

    if not settings.piper_voice:
        raise ValueError("Set MOURICE_PIPER_VOICE to a Piper .onnx voice file.")
    return Speaker(settings.piper_voice)
