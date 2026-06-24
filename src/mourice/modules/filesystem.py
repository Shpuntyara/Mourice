"""Filesystem tools — give Mourice access to the PC's files.

Reading and listing are free. Creating a new file is free. Overwriting and
deleting are gated behind a confirmer (the user approves), per the action-safety
rule ("Безопасность действий"). Scope is the whole machine (owner's choice).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from mourice.log import logger

from .base import Confirmer, Tool, ToolParameter, deny_all

__all__ = ["DeletePathTool", "ListDirTool", "ReadFileTool", "WriteFileTool"]

_MAX_READ_CHARS = 20000


class ListDirTool(Tool):
    """List files and folders in a directory."""

    name = "list_dir"
    description = "List the files and subfolders in a directory on the PC."
    parameters = (ToolParameter("path", "string", "Absolute directory path."),)

    def run(self, arguments: dict[str, Any]) -> str:
        path = Path(str(arguments.get("path", "")).strip())
        if not path.is_dir():
            return f"Error: not a directory: {path}"
        entries = []
        for item in sorted(path.iterdir()):
            kind = "dir " if item.is_dir() else "file"
            entries.append(f"[{kind}] {item.name}")
        return "\n".join(entries) if entries else "(empty)"


class ReadFileTool(Tool):
    """Read the contents of a text file."""

    name = "read_file"
    description = "Read the text contents of a file on the PC."
    parameters = (ToolParameter("path", "string", "Absolute file path."),)

    def run(self, arguments: dict[str, Any]) -> str:
        path = Path(str(arguments.get("path", "")).strip())
        if not path.is_file():
            return f"Error: file not found: {path}"
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"Error reading file: {exc}"
        if len(text) > _MAX_READ_CHARS:
            return text[:_MAX_READ_CHARS] + "\n…(truncated)"
        return text


class WriteFileTool(Tool):
    """Create or overwrite a file. Overwriting needs confirmation."""

    name = "write_file"
    description = (
        "Write text to a file on the PC. Creating a new file is allowed; "
        "overwriting an existing file requires user confirmation."
    )
    parameters = (
        ToolParameter("path", "string", "Absolute file path."),
        ToolParameter("content", "string", "Text content to write."),
    )

    def __init__(self, confirm: Confirmer = deny_all) -> None:
        self._confirm = confirm

    def run(self, arguments: dict[str, Any]) -> str:
        path = Path(str(arguments.get("path", "")).strip())
        content = arguments.get("content")
        if not str(path):
            return "Error: 'path' is required."
        if content is None:
            return "Error: 'content' is required."
        if path.is_file() and not self._confirm(f"Overwrite file {path}?"):
            return "Cancelled: overwrite not confirmed."
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(content), encoding="utf-8")
        except OSError as exc:
            return f"Error writing file: {exc}"
        logger.bind(path=str(path)).info("File written")
        return f"Wrote {path}"


class DeletePathTool(Tool):
    """Delete a file or folder. Always needs confirmation."""

    name = "delete_path"
    description = "Delete a file or folder on the PC. Always requires user confirmation."
    parameters = (ToolParameter("path", "string", "Absolute path to delete."),)

    def __init__(self, confirm: Confirmer = deny_all) -> None:
        self._confirm = confirm

    def run(self, arguments: dict[str, Any]) -> str:
        path = Path(str(arguments.get("path", "")).strip())
        if not path.exists():
            return f"Error: path not found: {path}"
        if not self._confirm(f"Delete {path}? This cannot be undone."):
            return "Cancelled: deletion not confirmed."
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            return f"Error deleting: {exc}"
        logger.bind(path=str(path)).warning("Path deleted")
        return f"Deleted {path}"
