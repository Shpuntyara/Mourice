"""Application wiring: build a fully-configured Mourice orchestrator.

Single place that assembles the provider, memory store, tools, context builder
and router from settings, so interfaces (terminal, Telegram, future UI) share
identical wiring.
"""

from __future__ import annotations

from mourice.config import Settings
from mourice.core import ContextBuilder, Orchestrator
from mourice.core.prompt import DEFAULT_LANGUAGE
from mourice.llm import ModelRoute, ModelRouter, OllamaProvider
from mourice.memory import build_store
from mourice.modules import (
    Confirmer,
    DeletePathTool,
    ListDirTool,
    ReadFileTool,
    ReadNoteTool,
    RunCommandTool,
    SearchMemoryTool,
    SendFileTool,
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
    voice_enabled: bool = False,
    send_file_tool: SendFileTool | None = None,
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
        if send_file_tool is not None:
            tools.append(send_file_tool)

    context = ContextBuilder(language=language, voice_enabled=voice_enabled)
    routes = []
    if settings.tool_model:
        routes.append(ModelRoute(
            keywords=(
                "файл", "папк", "директори", "создай файл", "запиши", "прочитай",
                "покажи", "рабочий стол", "downloads", "documents", "скачки",
                "терминал", "команд", "запусти", "выполни", "удали", "переименуй",
                "file", "folder", "directory", "desktop", "run", "execute", "delete",
            ),
            model=settings.tool_model,
        ))
    router = ModelRouter(settings.default_model, routes)
    return Orchestrator(
        provider,
        ToolRegistry(tools),
        context,
        router=router,
        history_path=settings.history_file or None,
    )
