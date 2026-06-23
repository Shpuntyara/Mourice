"""``read_note`` and ``write_note`` tools for the Obsidian vault.

Reading is free. Creating a new note is free. Overwriting an existing note is
gated behind an explicit ``overwrite`` flag, reflecting the action-safety rule
("Безопасность действий": irreversible changes need explicit intent).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mourice.log import logger

from .base import Tool, ToolParameter

__all__ = ["ReadNoteTool", "WriteNoteTool"]


def _resolve_in_vault(vault: Path, rel_path: str) -> Path | None:
    """Resolve ``rel_path`` inside the vault, or None if it escapes the vault."""
    candidate = (vault / rel_path).resolve()
    vault_root = vault.resolve()
    if candidate == vault_root or vault_root not in candidate.parents:
        return None
    return candidate


class ReadNoteTool(Tool):
    """Read the full content of a note from the vault."""

    name = "read_note"
    description = "Read the full markdown content of a note by its vault-relative path."
    parameters = (ToolParameter("path", "string", "Vault-relative path, e.g. 'Профиль/Я.md'."),)

    def __init__(self, vault_path: str | Path) -> None:
        self._vault = Path(vault_path)

    def run(self, arguments: dict[str, Any]) -> str:
        rel = str(arguments.get("path", "")).strip()
        if not rel:
            return "Error: 'path' is required."
        target = _resolve_in_vault(self._vault, rel)
        if target is None:
            return "Error: path is outside the vault."
        if not target.is_file():
            return f"Error: note not found: {rel}"
        return target.read_text(encoding="utf-8")


class WriteNoteTool(Tool):
    """Create or update a note. Overwriting an existing note requires overwrite=true."""

    name = "write_note"
    description = (
        "Create a new note or update an existing one. Creating is free; "
        "overwriting an existing note requires 'overwrite' set to true."
    )
    parameters = (
        ToolParameter("path", "string", "Vault-relative path, e.g. 'Входящие/idea.md'."),
        ToolParameter("content", "string", "Full markdown content to write."),
        ToolParameter(
            "overwrite", "boolean", "Allow overwriting an existing note.", required=False
        ),
    )

    def __init__(self, vault_path: str | Path) -> None:
        self._vault = Path(vault_path)

    def run(self, arguments: dict[str, Any]) -> str:
        rel = str(arguments.get("path", "")).strip()
        content = arguments.get("content")
        if not rel:
            return "Error: 'path' is required."
        if content is None:
            return "Error: 'content' is required."
        target = _resolve_in_vault(self._vault, rel)
        if target is None:
            return "Error: path is outside the vault."

        exists = target.is_file()
        if exists and not bool(arguments.get("overwrite", False)):
            return f"Note '{rel}' already exists. Set overwrite=true to replace it."

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding="utf-8")
        logger.bind(path=rel, overwritten=exists).info("Note written")
        return f"{'Updated' if exists else 'Created'} note: {rel}"
