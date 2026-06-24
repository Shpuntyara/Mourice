"""Speech-to-text via faster-whisper (local, multilingual).

Wraps a Whisper model behind a small ``Transcriber`` so it can be injected in
tests. The model is loaded lazily on first use (downloads once).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from mourice.log import logger

if TYPE_CHECKING:
    import numpy as np

__all__ = ["Transcriber"]


class Transcriber:
    """Transcribes int16 mono audio to text with faster-whisper."""

    def __init__(
        self,
        model_size: str = "small",
        *,
        language: str = "ru",
        device: str = "cpu",
        compute_type: str = "int8",
        model: Any | None = None,
    ) -> None:
        self._model_size = model_size
        self._language = language
        self._device = device
        self._compute_type = compute_type
        self._model = model

    def _get_model(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.bind(model=self._model_size).info("Loading Whisper model")
            self._model = WhisperModel(
                self._model_size, device=self._device, compute_type=self._compute_type
            )
        return self._model

    def transcribe(self, samples: np.ndarray[Any, Any], *, sample_rate: int = 16000) -> str:
        """Transcribe int16 mono samples (16 kHz) to text."""
        import numpy as np

        if samples.size == 0:
            return ""
        audio = samples.astype(np.float32) / 32768.0
        return self._run(audio)

    def transcribe_file(self, path: str | Path) -> str:
        """Transcribe an audio file (any format faster-whisper can decode, e.g. OGG/Opus)."""
        return self._run(str(path))

    def _run(self, audio: Any) -> str:
        segments, _info = self._get_model().transcribe(audio, language=self._language)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        logger.bind(chars=len(text)).debug("Transcribed audio")
        return text
