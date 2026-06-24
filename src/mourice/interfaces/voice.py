"""Voice interface — talk to Mourice by voice.

Push-to-talk loop: record → STT → orchestrator → TTS. Just another adapter over
the shared orchestrator (see "Архитектура — обзор"). Dependencies are injectable
for testing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from rich.console import Console

from mourice.app import build_orchestrator
from mourice.config import Settings
from mourice.voice import Transcriber, VoiceSpeaker, build_speaker, record_until_enter

if TYPE_CHECKING:
    from mourice.core import Orchestrator

__all__ = ["run_voice"]

_QUIT = {"q", "quit", "exit", "выход"}


def run_voice(
    settings: Settings,
    *,
    console: Console | None = None,
    orchestrator: Orchestrator | None = None,
    transcriber: Transcriber | None = None,
    speaker: VoiceSpeaker | None = None,
    recorder: Callable[[], Any] | None = None,
) -> None:
    """Run the push-to-talk voice loop."""
    console = console or Console()

    if speaker is None:
        try:
            speaker = build_speaker(settings)
        except ValueError as exc:
            console.print(f"[red]{exc}[/]")
            return

    orchestrator = orchestrator or build_orchestrator(settings)
    transcriber = transcriber or Transcriber(
        settings.whisper_model, language=settings.voice_language
    )
    record = recorder or record_until_enter

    console.print(
        "[bold cyan]Голосовой Морис.[/] Enter — говорить (Enter ещё раз — стоп), q — выход."
    )

    while True:
        cmd = console.input("[bold]» [/]").strip().lower()
        if cmd in _QUIT:
            console.print("[dim]Пока![/]")
            return

        samples = record()
        text = transcriber.transcribe(samples)
        if not text:
            console.print("[dim]…не расслышал, повтори.[/]")
            continue

        console.print(f"[bold]Ты:[/] {text}")
        reply = orchestrator.run(text)
        console.print(f"[bold cyan]Морис:[/] {reply}")
        speaker.say(reply)
