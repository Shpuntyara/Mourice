"""Application wiring: build a fully-configured Mourice orchestrator.

Single place that assembles the provider, memory store, tools, context builder
and router from settings, so interfaces (terminal, Telegram, future UI) share
identical wiring.
"""

from __future__ import annotations

from mourice.config import Settings
from mourice.core import ContextBuilder, Orchestrator
from mourice.core.prompt import DEFAULT_LANGUAGE
from mourice.llm import ModelRouter, OllamaProvider
from mourice.memory import build_store
from mourice.modules import (
    Confirmer,
    DeletePathTool,
    ListDirTool,
    ReadFileTool,
    ReadNoteTool,
    RunCommandTool,
    SearchMemoryTool,
    Tool,
    ToolRegistry,
    WriteFileTool,
    WriteNoteTool,
    deny_all,
)

__all__ = ["build_orchestrator"]


def build_orchestrator(
    settings: Settings,
    *,
    language: str = DEFAULT_LANGUAGE,
    confirmer: Confirmer = deny_all,
) -> Orchestrator:
    """Assemble the full Mourice orchestrator from settings.

    ``confirmer`` gates dangerous system actions (overwrite/delete/shell). Defaults
    to deny — interfaces that support a human prompt (e.g. terminal) pass their own.
    """
    provider = OllamaProvider(settings.ollama_host, settings.default_model, timeout=300.0)
    store = build_store(settings)

    tools: list[Tool] = [
        SearchMemoryTool(store),
        ReadNoteTool(settings.obsidian_vault),
        WriteNoteTool(settings.obsidian_vault),
    ]
    if settings.system_tools:
        tools += [
            ListDirTool(),
            ReadFileTool(),
            WriteFileTool(confirmer),
            DeletePathTool(confirmer),
            RunCommandTool(confirmer),
        ]

    context = ContextBuilder(language=language)
    router = ModelRouter(settings.default_model)
    return Orchestrator(provider, ToolRegistry(tools), context, router=router)
