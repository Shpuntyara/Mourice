"""Model router — chooses which LLM to use per task.

Phase 1 is a stub: a single default model, but with the interface and a simple
keyword-rule mechanism in place so Mourice can later swap models by task
(code → coder model, reasoning → stronger model). See "Стратегия выбора моделей".
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = ["ModelRoute", "ModelRouter"]


@dataclass(frozen=True)
class ModelRoute:
    """If any keyword appears in the input, use ``model``."""

    keywords: tuple[str, ...]
    model: str


class ModelRouter:
    """Selects a model for a given user input.

    With no routes it always returns the default model (the Phase 1 stub).
    Routes enable simple rule-based selection without touching the orchestrator.
    """

    def __init__(self, default_model: str, routes: Sequence[ModelRoute] = ()) -> None:
        self._default = default_model
        self._routes = tuple(routes)

    def select(self, text: str) -> str:
        """Return the model name to use for this input."""
        lowered = text.lower()
        for route in self._routes:
            if any(keyword.lower() in lowered for keyword in route.keywords):
                return route.model
        return self._default

    @property
    def default_model(self) -> str:
        return self._default
