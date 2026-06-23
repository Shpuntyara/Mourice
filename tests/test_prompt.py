"""Tests for the system prompt builder."""

from __future__ import annotations

from mourice.core import build_system_prompt


def test_prompt_has_identity_and_honesty() -> None:
    prompt = build_system_prompt()
    assert "Морис" in prompt
    assert "Честность" in prompt or "честно" in prompt.lower()
    assert "search_memory" in prompt


def test_language_russian_default() -> None:
    assert "русском" in build_system_prompt()
    assert "русском" in build_system_prompt("ru")


def test_language_polish() -> None:
    assert "polsku" in build_system_prompt("pl")


def test_language_english() -> None:
    assert "English" in build_system_prompt("en")


def test_unknown_language_falls_back_to_default() -> None:
    assert build_system_prompt("xx") == build_system_prompt("ru")
