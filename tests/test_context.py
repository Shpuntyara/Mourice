"""Tests for the context builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mourice.core import ContextBuilder
from mourice.llm import Message


def _no_paths() -> Path:
    """Return a path to a non-existent file so paths block is skipped."""
    return Path("/nonexistent/paths.json")


def test_system_first_user_last() -> None:
    messages = ContextBuilder(paths_file=_no_paths()).build([], "привет")
    assert messages[0].role == "system"
    assert messages[-1].role == "user"
    assert messages[-1].content == "привет"


def test_history_included_and_truncated() -> None:
    history = [Message("user" if i % 2 == 0 else "assistant", f"m{i}") for i in range(20)]
    builder = ContextBuilder(max_history_messages=4, paths_file=_no_paths())
    messages = builder.build(history, "now")

    # system + 4 history + user
    assert len(messages) == 6
    contents = [m.content for m in messages]
    assert "m19" in contents and "m16" in contents
    assert "m0" not in contents  # truncated


def test_retrieved_context_injected() -> None:
    messages = ContextBuilder(paths_file=_no_paths()).build([], "вопрос", retrieved=["факт A", "факт B"])
    system_blocks = [m.content for m in messages if m.role == "system"]
    assert any("факт A" in b and "факт B" in b for b in system_blocks)


def test_no_retrieved_no_extra_system() -> None:
    messages = ContextBuilder(paths_file=_no_paths()).build([], "q")
    assert sum(1 for m in messages if m.role == "system") == 1


def test_language_affects_prompt() -> None:
    messages = ContextBuilder(language="pl", paths_file=_no_paths()).build([], "q")
    assert "polsku" in messages[0].content


def test_paths_injected_into_context() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"рабочий стол": "C:/Users/test/Desktop", "_comment": "ignored"}, f)
        tmp = Path(f.name)
    try:
        messages = ContextBuilder(paths_file=tmp).build([], "q")
        system_texts = " ".join(m.content for m in messages if m.role == "system")
        assert "рабочий стол" in system_texts
        assert "C:/Users/test/Desktop" in system_texts
        assert "_comment" not in system_texts
    finally:
        tmp.unlink(missing_ok=True)


def test_missing_paths_file_is_silent() -> None:
    messages = ContextBuilder(paths_file=_no_paths()).build([], "q")
    # no crash, just no extra system block
    assert messages[0].role == "system"
