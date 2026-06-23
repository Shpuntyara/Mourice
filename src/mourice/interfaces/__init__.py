"""Interface adapters: CLI, voice, Telegram, desktop UI. Core stays interface-agnostic."""

from .terminal import run_chat

__all__ = ["run_chat"]
