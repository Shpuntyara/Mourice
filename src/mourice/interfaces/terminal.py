"""Terminal REPL — chat with Mourice from the console.

The terminal is just an interface adapter over the shared orchestrator
(see "Архитектура — обзор"). Commands: /lang, /reset, /help, /quit.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console

from mourice.app import build_orchestrator
from mourice.config import Settings
from mourice.core.prompt import DEFAULT_LANGUAGE

__all__ = ["Command", "parse_command", "run_chat"]

_LANGUAGES = {"ru", "pl", "en"}


@dataclass(frozen=True)
class Command:
    """A parsed slash-command."""

    name: str
    arg: str = ""


def parse_command(line: str) -> Command | None:
    """Parse a ``/command [arg]`` line, or None if it's a normal message."""
    if not line.startswith("/"):
        return None
    parts = line[1:].strip().split(maxsplit=1)
    if not parts:
        return Command("")
    return Command(parts[0].lower(), parts[1] if len(parts) > 1 else "")


def run_chat(settings: Settings, *, console: Console | None = None) -> None:
    """Run the interactive chat loop."""
    console = console or Console()
    language = DEFAULT_LANGUAGE
    orchestrator = build_orchestrator(settings, language=language)

    console.print(
        f"[bold cyan]Морис[/] на [green]{settings.default_model}[/]. "
        "Команды: /lang ru|pl|en, /reset, /help, /quit"
    )

    while True:
        try:
            line = console.input("[bold]Ты:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Пока![/]")
            return
        if not line:
            continue

        command = parse_command(line)
        if command is not None:
            if command.name in {"quit", "exit", "q"}:
                console.print("[dim]Пока![/]")
                return
            if command.name == "reset":
                orchestrator.reset()
                console.print("[dim]История очищена.[/]")
                continue
            if command.name == "lang":
                if command.arg in _LANGUAGES:
                    language = command.arg
                    orchestrator = build_orchestrator(settings, language=language)
                    console.print(f"[dim]Язык: {language} (история сброшена).[/]")
                else:
                    console.print("[red]Использование: /lang ru|pl|en[/]")
                continue
            if command.name == "help":
                console.print("Команды: /lang ru|pl|en, /reset, /help, /quit")
                continue
            console.print(f"[red]Неизвестная команда: /{command.name}[/]")
            continue

        with console.status("[dim]Морис думает…[/]"):
            reply = orchestrator.run(line)
        console.print(f"[bold cyan]Морис:[/] {reply}")
