"""The orchestrator: Mourice's agent loop.

Coordinates the LLM, tools, memory context and conversation history. Custom
minimal loop (variant B). The model may call tools (function calling); the
orchestrator executes them and feeds results back until the model gives a final
answer. See the "Оркестратор" design note.
"""

from __future__ import annotations

import json
from pathlib import Path
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
        tool_choice: str | None = None,
    ) -> dict[str, Any]: ...


def _to_dict(message: Message) -> dict[str, Any]:
    return {"role": message.role, "content": message.content}


_ACTION_WORDS = (
    "создай", "создать", "напиши", "написать", "сделай", "сделать",
    "удали", "удалить", "открой", "открыть", "запусти", "запустить",
    "скопируй", "скопировать", "перемести", "переименуй", "измени",
    "добавь", "добавить", "вставь", "вставить", "запиши", "записать",
    "переместить", "скачай", "установи", "запусти", "выполни",
    "create", "write", "make", "delete", "remove", "copy", "move",
    "run", "execute", "open", "install", "download",
)


def _is_action_request(text: str) -> bool:
    """Return True if the user message looks like an action (not just a question)."""
    lower = text.lower()
    return any(w in lower for w in _ACTION_WORDS)


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
        history_path: str | Path | None = None,
    ) -> None:
        self._backend = backend
        self._registry = registry
        self._context = context_builder or ContextBuilder()
        self._model = model
        self._router = router
        self._max_iterations = max_iterations
        self._history_path = Path(history_path) if history_path else None
        self._history: list[Message] = self._load_history()

    def _load_history(self) -> list[Message]:
        if not self._history_path or not self._history_path.exists():
            return []
        try:
            data = json.loads(self._history_path.read_text(encoding="utf-8"))
            return [Message(m["role"], m["content"]) for m in data]
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            logger.warning("Conversation history unreadable; starting fresh")
            return []

    def _save_history(self) -> None:
        if not self._history_path:
            return
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [{"role": m.role, "content": m.content} for m in self._history]
        self._history_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def run(self, user_input: str) -> str:
        """Process one user message and return Mourice's final reply."""
        messages = [_to_dict(m) for m in self._context.build(self._history, user_input)]
        tools = self._registry.schemas() or None
        model = self._router.select(user_input) if self._router else self._model

        force_tool = tools and _is_action_request(user_input)
        logger.debug("Orchestrator run", input_len=len(user_input), force_tool=bool(force_tool), n_tools=len(tools) if tools else 0)
        for iteration in range(self._max_iterations):
            tc = "required" if (iteration == 0 and force_tool) else None
            reply = self._backend.chat_raw(messages, tools=tools, model=model, tool_choice=tc)
            tool_calls = reply.get("tool_calls")

            if not tool_calls:
                content = str(reply.get("content", "")).strip()
                self._history.append(Message("user", user_input))
                self._history.append(Message("assistant", content))
                self._save_history()
                return content

            messages.append(reply)
            for call in tool_calls:
                function = call.get("function", {})
                name = str(function.get("name", ""))
                arguments = _parse_arguments(function.get("arguments"))
                logger.bind(tool=name).info("Orchestrator calling tool")
                result = self._registry.execute(name, arguments)
                logger.bind(tool=name, result=result[:120]).debug("Tool result")
                messages.append({"role": "tool", "content": result, "tool_name": name})

        logger.warning("Max iterations reached without a final answer")
        return "Не смог завершить за отведённое число шагов. Попробуй переформулировать."

    @property
    def history(self) -> list[Message]:
        return list(self._history)

    def reset(self) -> None:
        """Clear conversation history."""
        self._history.clear()
        self._save_history()
