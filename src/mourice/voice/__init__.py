"""Voice subsystem: audio I/O, speech-to-text, text-to-speech.

Heavy/optional dependencies (sounddevice, faster-whisper, piper-tts) are
imported lazily inside functions so the package imports without the ``voice``
extra installed (keeps core + CI light).
"""

from .audio import play, play_wav, record_until_enter

__all__ = ["play", "play_wav", "record_until_enter"]
