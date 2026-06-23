"""Tests for the Obsidian vault reader."""

from __future__ import annotations

from pathlib import Path

from mourice.memory import Note, VaultReader, parse_frontmatter


def test_parse_frontmatter_basic() -> None:
    text = "---\ntitle: Hello\ntags: [a, b]\n---\n\nBody text here."
    fm, body = parse_frontmatter(text)
    assert fm == {"title": "Hello", "tags": ["a", "b"]}
    assert body == "Body text here."


def test_parse_frontmatter_none() -> None:
    text = "# Just a heading\n\nNo frontmatter."
    fm, body = parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_parse_frontmatter_crlf() -> None:
    text = "---\r\ntitle: Win\r\n---\r\n\r\nBody."
    fm, body = parse_frontmatter(text)
    assert fm == {"title": "Win"}
    assert body == "Body."


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_read_all(tmp_path: Path) -> None:
    _write(tmp_path / "a.md", "---\ntitle: Alpha\n---\nAlpha body")
    _write(tmp_path / "sub" / "b.md", "Beta body without frontmatter")
    _write(tmp_path / ".obsidian" / "config.md", "should be excluded")

    reader = VaultReader(tmp_path)
    notes = reader.read_all()

    assert len(notes) == 2
    titles = {n.title for n in notes}
    assert titles == {"Alpha", "b"}  # title from frontmatter, or filename stem


def test_read_note_relative_path(tmp_path: Path) -> None:
    _write(tmp_path / "folder" / "note.md", "---\ntags: [x]\n---\nhi")
    reader = VaultReader(tmp_path)
    note = reader.read_note(tmp_path / "folder" / "note.md")

    assert isinstance(note, Note)
    assert note.path == Path("folder/note.md")
    assert note.frontmatter == {"tags": ["x"]}
    assert note.body == "hi"


def test_missing_vault(tmp_path: Path) -> None:
    reader = VaultReader(tmp_path / "does-not-exist")
    try:
        reader.read_all()
    except FileNotFoundError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected FileNotFoundError")
