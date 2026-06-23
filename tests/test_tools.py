"""Tests for the tool contract and registry."""

from __future__ import annotations

from typing import Any

import pytest

from mourice.modules import Tool, ToolParameter, ToolRegistry


class EchoTool(Tool):
    name = "echo"
    description = "Echo the given text"
    parameters = (ToolParameter("text", "string", "text to echo"),)

    def run(self, arguments: dict[str, Any]) -> str:
        return f"echo: {arguments['text']}"


class BoomTool(Tool):
    name = "boom"
    description = "Always fails"

    def run(self, arguments: dict[str, Any]) -> str:
        raise RuntimeError("kaboom")


def test_schema_shape() -> None:
    schema = EchoTool().to_schema()
    assert schema["type"] == "function"
    fn = schema["function"]
    assert fn["name"] == "echo"
    assert fn["parameters"]["properties"]["text"]["type"] == "string"
    assert fn["parameters"]["required"] == ["text"]


def test_register_and_execute() -> None:
    registry = ToolRegistry([EchoTool()])
    assert "echo" in registry
    assert len(registry) == 1
    assert registry.execute("echo", {"text": "hi"}) == "echo: hi"


def test_unknown_tool_returns_error() -> None:
    registry = ToolRegistry()
    result = registry.execute("nope", {})
    assert "unknown tool" in result.lower()


def test_tool_error_is_caught() -> None:
    registry = ToolRegistry([BoomTool()])
    result = registry.execute("boom", {})
    assert "kaboom" in result


def test_duplicate_registration_raises() -> None:
    registry = ToolRegistry([EchoTool()])
    with pytest.raises(ValueError, match="already registered"):
        registry.register(EchoTool())


def test_schemas_list() -> None:
    registry = ToolRegistry([EchoTool()])
    schemas = registry.schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "echo"
