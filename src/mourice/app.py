"""Application wiring: build a fully-configured Mourice orchestrator.

Single place that assembles the provider, memory store, tools, context builder
and router from settings, so interfaces (terminal, future Telegram/UI) share
identical wiring.
"""

from __future__ import annotations

from mourice.config import Settings
from mourice.core import ContextBuilder, Orchestrator
from mourice.core.prompt import DEFAULT_LANGUAGE
from mourice.llm import ModelRouter, OllamaProvider
from mourice.memory import build_store
from mourice.modules import ReadNoteTool, SearchMemoryTool, ToolRegistry, WriteNoteTool

__all__ = ["build_orchestrator"]


def build_orchestrator(settings: Settings, *, language: str = DEFAULT_LANGUAGE) -> Orchestrator:
    """Assemble the full Mourice orchestrator from settings."""
    provider = OllamaProvider(settings.ollama_host, settings.default_model, timeout=300.0)
    store = build_store(settings)
    registry = ToolRegistry(
        [
            SearchMemoryTool(store),
            ReadNoteTool(settings.obsidian_vault),
            WriteNoteTool(settings.obsidian_vault),
        ]
    )
    context = ContextBuilder(language=language)
    router = ModelRouter(settings.default_model)
    return Orchestrator(provider, registry, context, router=router)
