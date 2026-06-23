"""LLM provider abstraction.

The orchestrator talks to models only through ``LLMProvider``, so the model is
a swappable resource (see the "Маршрутизация LLM" / "Стратегия выбора моделей"
design notes). Providers stream their output as an iterator of text chunks.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

__all__ = ["LLMProvider", "Message"]


@dataclass(frozen=True)
class Message:
    """A single chat message."""

    role: str  # "system" | "user" | "assistant"
    content: str


@runtime_checkable
class LLMProvider(Protocol):
    """Interface every LLM backend must implement."""

    def chat(self, messages: Iterable[Message], *, model: str | None = None) -> Iterator[str]:
        """Stream the assistant reply as text chunks.

        Args:
            messages: conversation so far.
            model: override the provider's default model (for the router).

        Yields:
            Pieces of the assistant's response as they are generated.
        """
        ...

    def complete(self, messages: Iterable[Message], *, model: str | None = None) -> str:
        """Return the full reply as a single string (convenience over ``chat``)."""
        ...
