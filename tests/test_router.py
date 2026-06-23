"""Tests for the model router."""

from __future__ import annotations

from mourice.llm import ModelRoute, ModelRouter


def test_default_when_no_routes() -> None:
    router = ModelRouter("qwen2.5:14b")
    assert router.select("anything at all") == "qwen2.5:14b"
    assert router.default_model == "qwen2.5:14b"


def test_keyword_route_matches() -> None:
    router = ModelRouter(
        "qwen2.5:14b",
        routes=[ModelRoute(keywords=("код", "python", "script"), model="qwen2.5-coder:7b")],
    )
    assert router.select("напиши python скрипт") == "qwen2.5-coder:7b"
    assert router.select("давай обсудим планы") == "qwen2.5:14b"


def test_first_matching_route_wins() -> None:
    router = ModelRouter(
        "base",
        routes=[
            ModelRoute(keywords=("code",), model="coder"),
            ModelRoute(keywords=("code",), model="other"),
        ],
    )
    assert router.select("write code") == "coder"


def test_case_insensitive() -> None:
    router = ModelRouter("base", routes=[ModelRoute(keywords=("Python",), model="coder")])
    assert router.select("PYTHON please") == "coder"
