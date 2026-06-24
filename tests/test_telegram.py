"""Tests for the Telegram interface helpers (no network / no PTB needed)."""

from __future__ import annotations

import pytest

from mourice.config import Settings
from mourice.interfaces.telegram import authorize, parse_lang, run_telegram, split_sentences


def test_authorize_accepts_owner() -> None:
    assert authorize(42, 42) is True


def test_authorize_rejects_other_user() -> None:
    assert authorize(7, 42) is False


def test_authorize_rejects_when_no_owner_set() -> None:
    # owner_id == 0 means "nobody"; even a user with id 0 is refused.
    assert authorize(0, 0) is False


def test_authorize_rejects_missing_user() -> None:
    assert authorize(None, 42) is False


@pytest.mark.parametrize("arg", ["ru", "PL", " en ", "En"])
def test_parse_lang_accepts_supported(arg: str) -> None:
    assert parse_lang(arg) in {"ru", "pl", "en"}


@pytest.mark.parametrize("arg", ["", "de", "xx", "russian"])
def test_parse_lang_rejects_unsupported(arg: str) -> None:
    assert parse_lang(arg) is None


def test_run_telegram_without_token_raises() -> None:
    settings = Settings(telegram_token="", telegram_owner_id=42)
    with pytest.raises(ValueError, match="MOURICE_TELEGRAM_TOKEN"):
        run_telegram(settings)


def test_split_sentences_basic() -> None:
    parts = split_sentences("Привет. Как дела? Всё отлично!")
    assert len(parts) == 3
    assert parts[0] == "Привет."


def test_split_sentences_single() -> None:
    assert split_sentences("Привет") == ["Привет"]


def test_split_sentences_merges_tiny_tail() -> None:
    # very short tail should be merged into last sentence
    parts = split_sentences("Нормально всё. Ок.")
    assert len(parts) == 1


def test_run_telegram_without_owner_raises() -> None:
    settings = Settings(telegram_token="dummy", telegram_owner_id=0)
    with pytest.raises(ValueError, match="MOURICE_TELEGRAM_OWNER_ID"):
        run_telegram(settings)
