"""Tests for the orchestrator agent loop with a fake backend."""

from __future__ import annotations

from typing import Any

from mourice.core import Orchestrator
from mourice.modules import Tool, ToolParameter, ToolRegistry


class _ClockTool(Tool):
    name = "get_time"
    description = "Return the current time"
    parameters = (ToolParameter("tz", "string", "timezone", required=False),)

    def run(self, arguments: dict[str, Any]) -> str:
        return "12:00"


class _FakeBackend:
    """Returns queued replies in order; records calls."""

    def __init__(self, replies: list[dict[str, Any]]) -> None:
        self._replies = replies
        self.calls: list[list[dict[str, Any]]] = []

    def chat_raw(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        self.calls.append(messages)
        return self._replies.pop(0)


def test_direct_answer_no_tools() -> None:
    backend = _FakeBackend([{"content": "Привет!"}])
    orch = Orchestrator(backend, ToolRegistry())
    assert orch.run("привет") == "Привет!"
    assert len(orch.history) == 2  # user + assistant


def test_tool_call_then_answer() -> None:
    backend = _FakeBackend(
        [
            {"content": "", "tool_calls": [{"function": {"name": "get_time", "arguments": {}}}]},
            {"content": "Сейчас 12:00."},
        ]
    )
    orch = Orchestrator(backend, ToolRegistry([_ClockTool()]))
    result = orch.run("который час?")

    assert result == "Сейчас 12:00."
    # second call must include the tool result message
    second_call = backend.calls[1]
    assert any(m.get("role") == "tool" and "12:00" in m.get("content", "") for m in second_call)


def test_arguments_as_json_string() -> None:
    backend = _FakeBackend(
        [
            {"tool_calls": [{"function": {"name": "get_time", "arguments": '{"tz": "UTC"}'}}]},
            {"content": "ok"},
        ]
    )
    orch = Orchestrator(backend, ToolRegistry([_ClockTool()]))
    assert orch.run("time?") == "ok"


def test_max_iterations_guard() -> None:
    loop_reply = {"tool_calls": [{"function": {"name": "get_time", "arguments": {}}}]}
    backend = _FakeBackend([dict(loop_reply) for _ in range(10)])
    orch = Orchestrator(backend, ToolRegistry([_ClockTool()]), max_iterations=3)
    result = orch.run("loop")
    assert "шаг" in result.lower()
    assert len(backend.calls) == 3


def test_history_persists_across_instances(tmp_path: Any) -> None:
    path = tmp_path / "conv.json"
    b1 = _FakeBackend([{"content": "ответ"}])
    Orchestrator(b1, ToolRegistry(), history_path=path).run("привет")

    b2 = _FakeBackend([{"content": "снова"}])
    orch2 = Orchestrator(b2, ToolRegistry(), history_path=path)
    assert any(m.content == "привет" for m in orch2.history)


def test_reset_clears_history() -> None:
    backend = _FakeBackend([{"content": "a"}, {"content": "b"}])
    orch = Orchestrator(backend, ToolRegistry())
    orch.run("one")
    orch.reset()
    assert orch.history == []
