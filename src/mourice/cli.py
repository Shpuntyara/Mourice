"""Command-line entry point for Mourice.

Commands:
- ``mourice``        — show status banner.
- ``mourice sync``   — sync the Obsidian vault into ChromaDB (``--reset`` for full rebuild).
"""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel

from mourice import __version__
from mourice.config import Settings, get_settings
from mourice.log import logger, setup_logging
from mourice.memory import sync_vault

console = Console()


def _banner(settings: Settings) -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]Mourice[/] v{__version__}\n"
            f"[dim]Personal AI assistant orchestrator[/]\n\n"
            f"default model: [green]{settings.default_model}[/]\n"
            f"ollama host:   [green]{settings.ollama_host}[/]\n\n"
            f"[yellow]Phase 1 — building the Terminal MVP.[/]",
            title="booting",
            border_style="cyan",
        )
    )


def _run_sync(settings: Settings, *, reset: bool) -> None:
    console.print("[cyan]Syncing vault → ChromaDB…[/]")
    result = sync_vault(settings, reset=reset)
    console.print(
        f"[green]Done.[/] notes: {result.notes_total} "
        f"(changed {result.notes_changed}, removed {result.notes_removed}), "
        f"chunks written: {result.chunks_written}"
    )


def main() -> None:
    """Entry point registered as the ``mourice`` console script."""
    parser = argparse.ArgumentParser(prog="mourice", description="Mourice assistant")
    sub = parser.add_subparsers(dest="command")
    sync_parser = sub.add_parser("sync", help="Sync the Obsidian vault into ChromaDB")
    sync_parser.add_argument("--reset", action="store_true", help="Full rebuild")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings)
    logger.bind(version=__version__, command=args.command or "banner").info("Mourice starting")

    if args.command == "sync":
        _run_sync(settings, reset=args.reset)
    else:
        _banner(settings)


if __name__ == "__main__":
    main()
