"""Assemble the message list sent to the LLM.

Combines the system prompt (personality), optionally-injected memory context
(RAG), recent conversation history, and the current user input. Keeps the
working context small by truncating history (see "Память и базы данных").
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from mourice.llm import Message

from .prompt import DEFAULT_LANGUAGE, build_system_prompt

__all__ = ["ContextBuilder"]

_DEFAULT_MAX_HISTORY = 10
_DEFAULT_PATHS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "paths.json"


def _load_paths(paths_file: Path) -> str | None:
    """Load path aliases from JSON and format as a compact reference block."""
    try:
        data = json.loads(paths_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    lines = [
        f"  {alias} → {path}"
        for alias, path in data.items()
        if not alias.startswith("_")
    ]
    if not lines:
        return None
    return "Известные пути (используй сразу, не ищи по диску):\n" + "\n".join(lines)


class ContextBuilder:
    """Builds the message list for one LLM turn."""

    def __init__(
        self,
        *,
        language: str = DEFAULT_LANGUAGE,
        max_history_messages: int = _DEFAULT_MAX_HISTORY,
        voice_enabled: bool = False,
        paths_file: Path | None = None,
    ) -> None:
        self._language = language
        self._max_history = max_history_messages
        self._voice_enabled = voice_enabled
        self._paths_file = paths_file if paths_file is not None else _DEFAULT_PATHS_FILE

    def build(
        self,
        history: Sequence[Message],
        user_input: str,
        *,
        retrieved: Sequence[str] | None = None,
    ) -> list[Message]:
        """Assemble messages: system → [paths] → [memory] → recent history → user input."""
        messages: list[Message] = [
            Message("system", build_system_prompt(self._language, voice_enabled=self._voice_enabled))
        ]

        paths_block = _load_paths(self._paths_file)
        if paths_block:
            messages.append(Message("system", paths_block))

        if retrieved:
            joined = "\n\n---\n\n".join(retrieved)
            messages.append(
                Message(
                    "system",
                    "Релевантные фрагменты из базы знаний владельца "
                    f"(используй, если уместно):\n\n{joined}",
                )
            )

        if self._max_history > 0:
            messages.extend(history[-self._max_history :])
        else:
            messages.extend(history)

        messages.append(Message("user", user_input))
        return messages
