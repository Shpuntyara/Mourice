"""Tests for the shell command tool (runner mocked, confirmation gated)."""

from __future__ import annotations

from mourice.modules import RunCommandTool


def _yes(_p: str) -> bool:
    return True


def _no(_p: str) -> bool:
    return False


def _fake_runner(command: str) -> tuple[int, str, str]:
    return 0, f"ran: {command}", ""


def test_requires_confirmation() -> None:
    tool = RunCommandTool(_no, runner=_fake_runner)
    assert "Cancelled" in tool.run({"command": "echo hi"})


def test_runs_when_confirmed() -> None:
    tool = RunCommandTool(_yes, runner=_fake_runner)
    out = tool.run({"command": "echo hi"})
    assert "exit 0" in out
    assert "ran: echo hi" in out


def test_empty_command() -> None:
    tool = RunCommandTool(_yes, runner=_fake_runner)
    assert "required" in tool.run({"command": "  "}).lower()


def test_stderr_included() -> None:
    def runner(command: str) -> tuple[int, str, str]:
        return 1, "", "boom"

    tool = RunCommandTool(_yes, runner=runner)
    out = tool.run({"command": "bad"})
    assert "exit 1" in out
    assert "boom" in out


def test_runner_exception_handled() -> None:
    def runner(command: str) -> tuple[int, str, str]:
        raise RuntimeError("kaboom")

    tool = RunCommandTool(_yes, runner=runner)
    assert "Error running command" in tool.run({"command": "x"})
