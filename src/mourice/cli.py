"""Command-line entry point for Mourice.

Phase 0 placeholder: prints a banner and confirms configuration loads.
The real terminal REPL arrives in Phase 1 (Terminal MVP).
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from mourice import __version__
from mourice.config import get_settings

console = Console()


def main() -> None:
    """Entry point registered as the ``mourice`` console script."""
    settings = get_settings()
    console.print(
        Panel.fit(
            f"[bold cyan]Mourice[/] v{__version__}\n"
            f"[dim]Personal AI assistant orchestrator[/]\n\n"
            f"default model: [green]{settings.default_model}[/]\n"
            f"ollama host:   [green]{settings.ollama_host}[/]\n\n"
            f"[yellow]Phase 0 — foundation. Terminal MVP coming in Phase 1.[/]",
            title="booting",
            border_style="cyan",
        )
    )


if __name__ == "__main__":
    main()
