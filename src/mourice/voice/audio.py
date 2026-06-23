"""Microphone capture and audio playback (sounddevice).

Push-to-talk: recording runs until the user presses Enter. All audio is mono
int16 at a configurable sample rate. Imports are lazy so the module loads
without the ``voice`` extra.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mourice.log import logger

if TYPE_CHECKING:
    import numpy as np

__all__ = ["DEFAULT_SAMPLE_RATE", "play", "play_wav", "record_until_enter"]

DEFAULT_SAMPLE_RATE = 16000  # what Whisper expects


def record_until_enter(
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    *,
    wait_for_enter: Any = None,
) -> np.ndarray[Any, Any]:
    """Record mono int16 audio from the default mic until Enter is pressed.

    ``wait_for_enter`` is injectable for testing (defaults to ``input``).
    Returns the recorded samples as a 1-D int16 numpy array.
    """
    import numpy as np
    import sounddevice as sd

    stopper = wait_for_enter or (lambda: input())
    frames: list[np.ndarray[Any, Any]] = []

    def callback(indata: np.ndarray[Any, Any], *_: Any) -> None:
        frames.append(indata.copy())

    stop = threading.Event()

    def waiter() -> None:
        stopper()
        stop.set()

    thread = threading.Thread(target=waiter, daemon=True)
    thread.start()

    logger.debug("Recording… (Enter to stop)")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", callback=callback):
        while not stop.is_set():
            sd.sleep(100)

    if not frames:
        return np.zeros(0, dtype=np.int16)
    return np.concatenate(frames, axis=0).flatten()


def play(samples: np.ndarray[Any, Any], sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
    """Play int16 audio samples through the default output device (blocking)."""
    import sounddevice as sd

    sd.play(samples, samplerate=sample_rate)
    sd.wait()


def play_wav(path: str | Path) -> None:
    """Play a WAV file through the default output device (blocking)."""
    import wave

    import numpy as np

    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        data = wav.readframes(wav.getnframes())
    samples = np.frombuffer(data, dtype=np.int16)
    play(samples, rate)
