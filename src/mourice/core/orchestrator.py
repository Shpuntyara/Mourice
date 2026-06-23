"""The orchestrator: Mourice's agent loop.

Coordinates the LLM, tools, memory context and conversation history. Custom
minimal loop (variant B). The model may call tools (function calling); the
orchestrator executes them and feeds results back until the model gives a final
answer. See the "Оркестратор" design note.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from mourice.llm import Message, ModelRouter
from mourice.log import logger
from mourice.modules import ToolRegistry

from .context import ContextBuilder

__all__ = ["ChatBackend", "Orchestrator"]


class ChatBackend(Protocol):
    """Minimal LLM interface the orchestrator needs (satisfied by OllamaProvider)."""

    def chat_raw(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]: ...


def _to_dict(message: Message) -> dict[str, Any]:
    return {"role": message.role, "content": message.content}


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


class Orchestrator:
    """Runs one user turn through the agent loop, keeping conversation history."""

    def __init__(
        self,
        backend: ChatBackend,
        registry: ToolRegistry,
        context_builder: ContextBuilder | None = None,
        *,
        model: str | None = None,
        router: ModelRouter | None = None,
        max_iterations: int = 5,
    ) -> None:
        self._backend = backend
        self._registry = registry
        self._context = context_builder or ContextBuilder()
        self._model = model
        self._router = router
        self._max_iterations = max_iterations
        self._history: list[Message] = []

    def run(self, user_input: str) -> str:
        """Process one user message and return Mourice's final reply."""
        messages = [_to_dict(m) for m in self._context.build(self._history, user_input)]
        tools = self._registry.schemas() or None
        model = self._router.select(user_input) if self._router else self._model

        for _ in range(self._max_iterations):
            reply = self._backend.chat_raw(messages, tools=tools, model=model)
            tool_calls = reply.get("tool_calls")

            if not tool_calls:
                content = str(reply.get("content", "")).strip()
                self._history.append(Message("user", user_input))
                self._history.append(Message("assistant", content))
                return content

            messages.append(reply)
            for call in tool_calls:
                function = call.get("function", {})
                name = str(function.get("name", ""))
                arguments = _parse_arguments(function.get("arguments"))
                logger.bind(tool=name).info("Orchestrator calling tool")
                result = self._registry.execute(name, arguments)
                messages.append({"role": "tool", "content": result, "tool_name": name})

        logger.warning("Max iterations reached without a final answer")
        return "Не смог завершить за отведённое число шагов. Попробуй переформулировать."

    @property
    def history(self) -> list[Message]:
        return list(self._history)

    def reset(self) -> None:
        """Clear conversation history."""
        self._history.clear()
