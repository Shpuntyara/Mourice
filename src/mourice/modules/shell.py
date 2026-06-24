"""Shell command tool — run commands on the PC (always confirmed).

Executes via PowerShell on Windows. Every command requires user confirmation
(it's the highest-risk capability). Output is captured and truncated.
"""

from __future__ import annotations

import subprocess
from typing import Any

from mourice.log import logger

from .base import Confirmer, Tool, ToolParameter, deny_all

__all__ = ["RunCommandTool"]

_MAX_OUTPUT = 8000
_TIMEOUT = 120


class RunCommandTool(Tool):
    """Run a shell command on the PC. Always requires confirmation."""

    name = "run_command"
    description = (
        "Run a shell command on the PC (PowerShell on Windows) and return its output. "
        "Always requires user confirmation. Use for system tasks the user asks for."
    )
    parameters = (ToolParameter("command", "string", "The command line to run."),)

    def __init__(
        self,
        confirm: Confirmer = deny_all,
        *,
        runner: Any | None = None,
    ) -> None:
        self._confirm = confirm
        self._runner = runner or self._default_runner

    @staticmethod
    def _default_runner(command: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def run(self, arguments: dict[str, Any]) -> str:
        command = str(arguments.get("command", "")).strip()
        if not command:
            return "Error: 'command' is required."
        if not self._confirm(f"Run command?\n  {command}"):
            return "Cancelled: command not confirmed."

        try:
            code, out, err = self._runner(command)
        except Exception as exc:  # noqa: BLE001 — surface failures to the LLM
            logger.bind(command=command).exception("Command failed")
            return f"Error running command: {exc}"

        logger.bind(command=command, code=code).info("Command executed")
        output = (out or "") + (("\n[stderr]\n" + err) if err else "")
        output = output.strip() or "(no output)"
        if len(output) > _MAX_OUTPUT:
            output = output[:_MAX_OUTPUT] + "\n…(truncated)"
        return f"exit {code}\n{output}"
