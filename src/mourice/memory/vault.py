"""Read notes from an Obsidian vault.

Loads ``.md`` files, splits YAML frontmatter from the body, and returns
structured ``Note`` objects. This is the source-of-truth side of memory
(see "Память и базы данных"); chunking and embedding come later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from mourice.log import logger

__all__ = ["Note", "VaultReader", "parse_frontmatter"]

_DEFAULT_EXCLUDES = (".obsidian", ".trash")


@dataclass(frozen=True)
class Note:
    """A single note loaded from the vault."""

    path: Path  # relative to the vault root (stable id)
    title: str
    body: str
    frontmatter: dict[str, Any] = field(default_factory=dict)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from the body.

    Returns ``(frontmatter, body)``. If there is no valid frontmatter block,
    returns ``({}, text)``.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return {}, normalized

    end = normalized.find("\n---", 4)
    if end == -1:
        return {}, normalized

    raw_fm = normalized[4:end]
    # body starts after the closing fence line
    rest = normalized[end + 4 :]
    body = rest.lstrip("\n")

    try:
        loaded = yaml.safe_load(raw_fm)
    except yaml.YAMLError:
        logger.warning("Failed to parse frontmatter; treating as no frontmatter")
        return {}, normalized

    frontmatter = loaded if isinstance(loaded, dict) else {}
    return frontmatter, body


class VaultReader:
    """Reads notes from an Obsidian vault directory."""

    def __init__(self, vault_path: str | Path, *, excludes: Iterable[str] = _DEFAULT_EXCLUDES):
        self.vault_path = Path(vault_path)
        self._excludes = set(excludes)

    def read_all(self) -> list[Note]:
        """Read every ``.md`` note in the vault (recursively), skipping excludes."""
        if not self.vault_path.is_dir():
            raise FileNotFoundError(f"Vault not found: {self.vault_path}")

        notes: list[Note] = []
        for md_path in sorted(self.vault_path.rglob("*.md")):
            if self._is_excluded(md_path):
                continue
            notes.append(self.read_note(md_path))
        logger.bind(count=len(notes), vault=str(self.vault_path)).info("Vault loaded")
        return notes

    def read_note(self, path: str | Path) -> Note:
        """Read and parse a single note."""
        abs_path = Path(path)
        text = abs_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        try:
            rel_path = abs_path.relative_to(self.vault_path)
        except ValueError:
            rel_path = abs_path
        title_value = frontmatter.get("title")
        title = str(title_value) if title_value else abs_path.stem
        return Note(path=rel_path, title=title, body=body, frontmatter=frontmatter)

    def _is_excluded(self, path: Path) -> bool:
        rel = path.relative_to(self.vault_path)
        return any(part in self._excludes for part in rel.parts)
