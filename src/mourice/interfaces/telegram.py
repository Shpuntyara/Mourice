"""Telegram interface — talk to Mourice from Telegram (Phase 3).

Just another adapter over the shared orchestrator (see "Архитектура — обзор").
Single-owner: only ``telegram_owner_id`` may use the bot, since the orchestrator
can write to the vault. Text and voice messages are supported; voice notes are
transcribed with the same faster-whisper STT used by the voice loop.

Heavy/optional deps (python-telegram-bot, faster-whisper, piper) are imported
lazily inside ``run_telegram`` so the package imports without the ``telegram`` /
``voice`` extras installed. The pure helpers below stay import-light for tests.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mourice.config import Settings
from mourice.log import logger

if TYPE_CHECKING:
    from mourice.core import Orchestrator
    from mourice.voice import Transcriber, VoiceSpeaker

__all__ = ["authorize", "parse_lang", "run_telegram"]

_LANGUAGES = {"ru", "pl", "en"}

_DENIED = "Извини, этот бот личный — у тебя нет доступа."
_WELCOME = (
    "Привет, я Морис. Пиши текстом или голосовым. "
    "Команды: /reset — очистить историю, /lang ru|pl|en — сменить язык, /help."
)
_HELP = "Команды: /reset — очистить историю, /lang ru|pl|en — сменить язык, /help."
_NO_SPEECH = "…не расслышал, попробуй ещё раз."


def authorize(user_id: int | None, owner_id: int) -> bool:
    """Return True iff ``user_id`` is the configured owner (and an owner is set)."""
    return owner_id != 0 and user_id == owner_id


def parse_lang(arg: str) -> str | None:
    """Parse a ``/lang`` argument into a supported language code, or None."""
    code = arg.strip().lower()
    return code if code in _LANGUAGES else None


def run_telegram(
    settings: Settings,
    *,
    orchestrator: Orchestrator | None = None,
    transcriber: Transcriber | None = None,
    speaker: VoiceSpeaker | None = None,
) -> None:
    """Run the Telegram bot (long-polling). Blocks until interrupted."""
    if not settings.telegram_token:
        raise ValueError("Set MOURICE_TELEGRAM_TOKEN to run the Telegram bot.")
    if settings.telegram_owner_id == 0:
        raise ValueError("Set MOURICE_TELEGRAM_OWNER_ID — the bot refuses everyone otherwise.")

    import asyncio

    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    from mourice.app import build_orchestrator

    agent = orchestrator or build_orchestrator(settings)
    owner_id = settings.telegram_owner_id

    # Voice deps are built lazily on first voice message to keep startup light.
    state: dict[str, Any] = {"transcriber": transcriber, "speaker": speaker}

    def _get_transcriber() -> Transcriber:
        if state["transcriber"] is None:
            from mourice.voice import Transcriber as _Transcriber

            state["transcriber"] = _Transcriber(
                settings.whisper_model, language=settings.voice_language
            )
        return state["transcriber"]  # type: ignore[no-any-return]

    def _get_speaker() -> VoiceSpeaker | None:
        if not settings.telegram_voice_reply:
            return None
        if state["speaker"] is None:
            from mourice.voice import build_speaker

            state["speaker"] = build_speaker(settings)
        return state["speaker"]  # type: ignore[no-any-return]

    async def _guard(update: Update) -> bool:
        user = update.effective_user
        if authorize(user.id if user else None, owner_id):
            return True
        logger.bind(user_id=user.id if user else None).warning("Telegram access denied")
        if update.message:
            await update.message.reply_text(_DENIED)
        return False

    async def _reply(update: Update, text: str) -> None:
        if not update.message:
            return
        await update.message.reply_text(text)
        speaker_ = _get_speaker()
        if speaker_ is not None and text.strip():
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    wav = Path(tmp) / "reply.wav"
                    await asyncio.to_thread(speaker_.save, text, wav)  # type: ignore[attr-defined]
                    with wav.open("rb") as fh:
                        await update.message.reply_audio(fh)
            except Exception:  # noqa: BLE001 — voice reply is best-effort
                logger.exception("Telegram voice reply failed")

    async def on_start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message:
            return
        await update.message.reply_text(_WELCOME)

    async def on_help(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message:
            return
        await update.message.reply_text(_HELP)

    async def on_reset(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message:
            return
        agent.reset()
        await update.message.reply_text("История очищена.")

    async def on_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message:
            return
        lang = parse_lang(ctx.args[0]) if ctx.args else None
        if lang is None:
            await update.message.reply_text("Использование: /lang ru|pl|en")
            return
        # Rebuild on the configured agent only when we own it (default wiring).
        nonlocal agent
        agent = build_orchestrator(settings, language=lang)
        await update.message.reply_text(f"Язык: {lang} (история сброшена).")

    async def on_text(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message or not update.message.text:
            return
        await update.message.chat.send_action("typing")
        reply = await asyncio.to_thread(agent.run, update.message.text)
        await _reply(update, reply)

    async def on_voice(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not await _guard(update) or not update.message or not update.message.voice:
            return
        await update.message.chat.send_action("typing")
        tg_file = await update.message.voice.get_file()
        with tempfile.TemporaryDirectory() as tmp:
            ogg = Path(tmp) / "voice.ogg"
            await tg_file.download_to_drive(ogg)
            text = await asyncio.to_thread(_get_transcriber().transcribe_file, ogg)
        if not text:
            await update.message.reply_text(_NO_SPEECH)
            return
        await update.message.reply_text(f"🗣 {text}")
        reply = await asyncio.to_thread(agent.run, text)
        await _reply(update, reply)

    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(CommandHandler("help", on_help))
    app.add_handler(CommandHandler("reset", on_reset))
    app.add_handler(CommandHandler("lang", on_lang))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.bind(owner_id=owner_id).info("Telegram bot starting (long-polling)")
    app.run_polling()
