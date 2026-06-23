"""Tests for terminal command parsing."""

from __future__ import annotations

from mourice.interfaces.terminal import parse_command


def test_normal_message_is_not_command() -> None:
    assert parse_command("привет, как дела?") is None


def test_simple_command() -> None:
    cmd = parse_command("/quit")
    assert cmd is not None
    assert cmd.name == "quit"
    assert cmd.arg == ""


def test_command_with_arg() -> None:
    cmd = parse_command("/lang pl")
    assert cmd is not None
    assert cmd.name == "lang"
    assert cmd.arg == "pl"


def test_command_is_lowercased() -> None:
    cmd = parse_command("/RESET")
    assert cmd is not None
    assert cmd.name == "reset"


def test_arg_keeps_rest_of_line() -> None:
    cmd = parse_command("/note this is a long argument")
    assert cmd is not None
    assert cmd.name == "note"
    assert cmd.arg == "this is a long argument"
