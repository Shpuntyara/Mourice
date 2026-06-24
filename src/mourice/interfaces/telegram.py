"""Telegram interface — talk to Mourice from Telegram (Phase 3).

Just another adapter over the shared orchestrator (see "Архитектура — обзор").
Single-owner: only ``telegram_owner_id`` may use the bot, since the orchestrator
can write to the vault. Text and voice messages are supported; voice notes are
transcribed with the same faster-whisper STT used by the voice loop.

Built on aiogram (per the "Фаза 3 — Telegram" design note). Heavy/optional deps
(aiogram, faster-whisper, piper) are imported lazily inside ``run_telegram`` so
the package imports without the ``telegram`` / ``voice`` extras installed. The
pure helpers below stay import-light for tests.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mourice.config import Settings
from mourice.log import logger

if TYPE_CHECKING:
    from mourice.core import Orchestrator
    from mourice.voice import Transcriber, VoiceSpeaker

__all__ = ["authorize", "parse_lang", "run_telegram", "split_sentences"]

_SENTENCE_RE = re.compile(r'(?<=[.!?…])\s+(?=[^\s])')
_MIN_SENTENCE_LEN = 4


def split_sentences(text: str) -> list[str]:
    """Split text into sentences for streaming TTS delivery."""
    parts = _SENTENCE_RE.split(text.strip())
    result: list[str] = []
    buf = ""
    for part in parts:
        buf = (buf + " " + part).strip() if buf else part
        if len(buf) >= _MIN_SENTENCE_LEN:
            result.append(buf)
            buf = ""
    if buf:
        if result:
            result[-1] += " " + buf  # merge tiny tail into previous
        else:
            result.append(buf)
    return result or [text]

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


def parse_lang(arg: str | None) -> str | None:
    """Parse a ``/lang`` argument into a supported language code, or None."""
    code = (arg or "").strip().lower()
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

    from aiogram import Bot, Dispatcher, F
    from aiogram.filters import Command, CommandObject
    from aiogram.types import FSInputFile, Message

    from mourice.app import build_orchestrator
    from mourice.modules import SendFileTool, deny_all

    # Owner is the only user, so optionally approve dangerous ops without a prompt.
    confirmer = (lambda _p: True) if settings.telegram_allow_commands else deny_all

    send_file_tool: SendFileTool | None = None
    if orchestrator is None:
        send_file_tool = SendFileTool()
        agent = build_orchestrator(
            settings,
            confirmer=confirmer,
            voice_enabled=settings.telegram_voice_reply,
            send_file_tool=send_file_tool,
        )
    else:
        agent = orchestrator
    owner_id = settings.telegram_owner_id

    def _arm_sender(message: Message) -> None:
        """Point send_file_tool at the current message before agent.run()."""
        if send_file_tool is None:
            return
        loop = asyncio.get_running_loop()

        def _sync_send(path: Path) -> None:
            fut = asyncio.run_coroutine_threadsafe(
                message.answer_document(FSInputFile(str(path))), loop
            )
            fut.result(timeout=60)

        send_file_tool.set_sender(_sync_send)

    def _disarm_sender() -> None:
        if send_file_tool is not None:
            send_file_tool.set_sender(None)

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

    def _authorized(message: Message) -> bool:
        return authorize(message.from_user.id if message.from_user else None, owner_id)

    async def _deny(message: Message) -> None:
        logger.bind(user_id=message.from_user.id if message.from_user else None).warning(
            "Telegram access denied"
        )
        await message.answer(_DENIED)

    async def _reply(message: Message, text: str) -> None:
        speaker_ = _get_speaker()
        if speaker_ is not None and text.strip():
            sentences = split_sentences(text)
            sent_any = False
            for sentence in sentences:
                if not sentence.strip():
                    continue
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        wav = Path(tmp) / "reply.wav"
                        await asyncio.to_thread(speaker_.save, sentence, wav)  # type: ignore[attr-defined]
                        await message.answer_audio(FSInputFile(wav))
                        sent_any = True
                except Exception:  # noqa: BLE001 — voice reply is best-effort
                    logger.exception("Telegram voice reply failed for sentence")
            if sent_any:
                return
        await message.answer(text)

    async def on_start(message: Message) -> None:
        if not _authorized(message):
            return await _deny(message)
        await message.answer(_WELCOME)

    async def on_help(message: Message) -> None:
        if not _authorized(message):
            return await _deny(message)
        await message.answer(_HELP)

    async def on_reset(message: Message) -> None:
        if not _authorized(message):
            return await _deny(message)
        agent.reset()
        await message.answer("История очищена.")

    async def on_lang(message: Message, command: CommandObject) -> None:
        if not _authorized(message):
            return await _deny(message)
        lang = parse_lang(command.args)
        if lang is None:
            await message.answer("Использование: /lang ru|pl|en")
            return
        nonlocal agent
        agent = build_orchestrator(settings, language=lang, confirmer=confirmer)
        await message.answer(f"Язык: {lang} (история сброшена).")

    async def on_text(message: Message) -> None:
        if not _authorized(message):
            return await _deny(message)
        if not message.text:
            return
        await bot.send_chat_action(message.chat.id, "typing")
        _arm_sender(message)
        try:
            reply = await asyncio.to_thread(agent.run, message.text)
        finally:
            _disarm_sender()
        await _reply(message, reply)

    async def on_voice(message: Message) -> None:
        if not _authorized(message):
            return await _deny(message)
        if not message.voice:
            return
        await bot.send_chat_action(message.chat.id, "typing")
        with tempfile.TemporaryDirectory() as tmp:
            ogg = Path(tmp) / "voice.ogg"
            await bot.download(message.voice, destination=ogg)
            text = await asyncio.to_thread(_get_transcriber().transcribe_file, ogg)
        if not text:
            await message.answer(_NO_SPEECH)
            return
        await message.answer(f"🗣 {text}")
        _arm_sender(message)
        try:
            reply = await asyncio.to_thread(agent.run, text)
        finally:
            _disarm_sender()
        await _reply(message, reply)

    dp = Dispatcher()
    dp.message.register(on_start, Command("start"))
    dp.message.register(on_help, Command("help"))
    dp.message.register(on_reset, Command("reset"))
    dp.message.register(on_lang, Command("lang"))
    dp.message.register(on_voice, F.voice)
    dp.message.register(on_text, F.text & ~F.text.startswith("/"))

    bot = Bot(settings.telegram_token)
    logger.bind(owner_id=owner_id).info("Telegram bot starting (long-polling)")
    asyncio.run(dp.start_polling(bot))
