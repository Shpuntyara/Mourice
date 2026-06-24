"""Interface adapters: CLI, voice, Telegram, desktop UI. Core stays interface-agnostic."""

from .telegram import run_telegram
from .terminal import run_chat
from .voice import run_voice

__all__ = ["run_chat", "run_telegram", "run_voice"]
