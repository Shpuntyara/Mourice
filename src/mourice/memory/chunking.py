"""Split notes into retrieval chunks.

Chunks follow markdown headings so each piece is self-contained, and each
carries a breadcrumb (note title > heading path) so it stays meaningful out of
context — important for RAG quality. Large sections are split by paragraphs.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .vault import Note

__all__ = ["Chunk", "chunk_note", "chunk_notes"]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_DEFAULT_MAX_CHARS = 1500


@dataclass(frozen=True)
class Chunk:
    """A single retrieval unit derived from a note."""

    id: str
    text: str
    note_path: str
    note_title: str
    breadcrumb: str
    index: int
    frontmatter: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Section:
    headings: list[tuple[int, str]]  # (level, title) stack to this section
    lines: list[str]


def _split_sections(body: str) -> list[_Section]:
    sections: list[_Section] = []
    stack: list[tuple[int, str]] = []
    current = _Section(headings=[], lines=[])

    for line in body.split("\n"):
        match = _HEADING_RE.match(line)
        if match:
            if current.lines or current.headings:
                sections.append(current)
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current = _Section(headings=list(stack), lines=[line])
        else:
            current.lines.append(line)

    if current.lines or current.headings:
        sections.append(current)
    return sections


def _split_long(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    buffer = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(candidate) > max_chars and buffer:
            parts.append(buffer)
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        parts.append(buffer)
    return parts


def chunk_note(note: Note, *, max_chars: int = _DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Split a single note into heading-aware chunks."""
    chunks: list[Chunk] = []
    note_path = str(note.path).replace("\\", "/")

    for section in _split_sections(note.body):
        breadcrumb_parts = [note.title] + [title for _, title in section.headings]
        breadcrumb = " > ".join(breadcrumb_parts)
        content = "\n".join(section.lines).strip()
        if not content:
            continue

        for piece in _split_long(content, max_chars):
            index = len(chunks)
            chunks.append(
                Chunk(
                    id=f"{note_path}#{index}",
                    text=f"{breadcrumb}\n\n{piece}",
                    note_path=note_path,
                    note_title=note.title,
                    breadcrumb=breadcrumb,
                    index=index,
                    frontmatter=note.frontmatter,
                )
            )
    return chunks


def chunk_notes(notes: Iterable[Note], *, max_chars: int = _DEFAULT_MAX_CHARS) -> list[Chunk]:
    """Split many notes into chunks."""
    result: list[Chunk] = []
    for note in notes:
        result.extend(chunk_note(note, max_chars=max_chars))
    return result
