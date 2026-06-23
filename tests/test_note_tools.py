"""Tests for read_note / write_note tools."""

from __future__ import annotations

from pathlib import Path

from mourice.modules import ReadNoteTool, WriteNoteTool


def test_write_creates_note(tmp_path: Path) -> None:
    tool = WriteNoteTool(tmp_path)
    result = tool.run({"path": "Входящие/idea.md", "content": "# Idea\nhello"})
    assert "Created" in result
    assert (tmp_path / "Входящие" / "idea.md").read_text(encoding="utf-8") == "# Idea\nhello"


def test_write_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("old", encoding="utf-8")
    tool = WriteNoteTool(tmp_path)
    result = tool.run({"path": "a.md", "content": "new"})
    assert "overwrite=true" in result
    assert (tmp_path / "a.md").read_text(encoding="utf-8") == "old"  # unchanged


def test_write_overwrite_with_flag(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("old", encoding="utf-8")
    tool = WriteNoteTool(tmp_path)
    result = tool.run({"path": "a.md", "content": "new", "overwrite": True})
    assert "Updated" in result
    assert (tmp_path / "a.md").read_text(encoding="utf-8") == "new"


def test_read_note(tmp_path: Path) -> None:
    (tmp_path / "n.md").write_text("content here", encoding="utf-8")
    tool = ReadNoteTool(tmp_path)
    assert tool.run({"path": "n.md"}) == "content here"


def test_read_missing(tmp_path: Path) -> None:
    tool = ReadNoteTool(tmp_path)
    assert "not found" in tool.run({"path": "nope.md"}).lower()


def test_path_traversal_blocked(tmp_path: Path) -> None:
    secret = tmp_path.parent / "secret.md"
    secret.write_text("top secret", encoding="utf-8")
    tool = ReadNoteTool(tmp_path)
    result = tool.run({"path": "../secret.md"})
    assert "outside the vault" in result.lower()


def test_write_traversal_blocked(tmp_path: Path) -> None:
    tool = WriteNoteTool(tmp_path)
    result = tool.run({"path": "../escape.md", "content": "x"})
    assert "outside the vault" in result.lower()
    assert not (tmp_path.parent / "escape.md").exists()
