"""Tool (skill module) contract and registry.

Tools are how Mourice acts. The orchestrator exposes registered tools to the
LLM as function-calling schemas (Ollama/OpenAI style); when the model asks to
call one, the registry executes it. The core never hard-codes tool logic
(see the "Модульная система" design note).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from mourice.log import logger

__all__ = ["Tool", "ToolParameter", "ToolRegistry"]


@dataclass(frozen=True)
class ToolParameter:
    """One input parameter of a tool."""

    name: str
    type: str  # JSON-schema type: "string" | "integer" | "number" | "boolean"
    description: str
    required: bool = True


class Tool(ABC):
    """Base class for a callable skill.

    Subclasses set ``name``, ``description``, ``parameters`` and implement
    ``run``. ``run`` returns a string that is fed back to the LLM.
    """

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()

    @abstractmethod
    def run(self, arguments: dict[str, Any]) -> str:
        """Execute the tool with validated arguments and return a text result."""

    def to_schema(self) -> dict[str, Any]:
        """Return the function-calling schema (Ollama/OpenAI style)."""
        properties = {
            p.name: {"type": p.type, "description": p.description} for p in self.parameters
        }
        required = [p.name for p in self.parameters if p.required]
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """Holds the available tools and exposes them to the orchestrator."""

    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool
        logger.bind(tool=tool.name).debug("Tool registered")

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        """Function-calling schemas for every registered tool."""
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """Run a tool by name. Returns the tool's result or an error string."""
        tool = self._tools.get(name)
        if tool is None:
            logger.bind(tool=name).warning("Unknown tool requested")
            return f"Error: unknown tool '{name}'"
        try:
            return tool.run(arguments)
        except Exception as exc:  # noqa: BLE001 — surface tool errors to the LLM
            logger.bind(tool=name).exception("Tool execution failed")
            return f"Error running '{name}': {exc}"

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools
