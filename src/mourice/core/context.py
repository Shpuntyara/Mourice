"""Assemble the message list sent to the LLM.

Combines the system prompt (personality), optionally-injected memory context
(RAG), recent conversation history, and the current user input. Keeps the
working context small by truncating history (see "Память и базы данных").
"""

from __future__ import annotations

from collections.abc import Sequence

from mourice.llm import Message

from .prompt import DEFAULT_LANGUAGE, build_system_prompt

__all__ = ["ContextBuilder"]

_DEFAULT_MAX_HISTORY = 10


class ContextBuilder:
    """Builds the message list for one LLM turn."""

    def __init__(
        self,
        *,
        language: str = DEFAULT_LANGUAGE,
        max_history_messages: int = _DEFAULT_MAX_HISTORY,
    ) -> None:
        self._language = language
        self._max_history = max_history_messages

    def build(
        self,
        history: Sequence[Message],
        user_input: str,
        *,
        retrieved: Sequence[str] | None = None,
    ) -> list[Message]:
        """Assemble messages: system → [memory] → recent history → user input."""
        messages: list[Message] = [Message("system", build_system_prompt(self._language))]

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
