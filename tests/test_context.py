"""Tests for the context builder."""

from __future__ import annotations

from mourice.core import ContextBuilder
from mourice.llm import Message


def test_system_first_user_last() -> None:
    messages = ContextBuilder().build([], "привет")
    assert messages[0].role == "system"
    assert messages[-1].role == "user"
    assert messages[-1].content == "привет"


def test_history_included_and_truncated() -> None:
    history = [Message("user" if i % 2 == 0 else "assistant", f"m{i}") for i in range(20)]
    builder = ContextBuilder(max_history_messages=4)
    messages = builder.build(history, "now")

    # system + 4 history + user
    assert len(messages) == 6
    contents = [m.content for m in messages]
    assert "m19" in contents and "m16" in contents
    assert "m0" not in contents  # truncated


def test_retrieved_context_injected() -> None:
    messages = ContextBuilder().build([], "вопрос", retrieved=["факт A", "факт B"])
    system_blocks = [m.content for m in messages if m.role == "system"]
    assert any("факт A" in b and "факт B" in b for b in system_blocks)


def test_no_retrieved_no_extra_system() -> None:
    messages = ContextBuilder().build([], "q")
    assert sum(1 for m in messages if m.role == "system") == 1


def test_language_affects_prompt() -> None:
    messages = ContextBuilder(language="pl").build([], "q")
    assert "polsku" in messages[0].content
