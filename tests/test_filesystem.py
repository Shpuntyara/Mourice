"""Tests for filesystem tools (with confirmation)."""

from __future__ import annotations

from pathlib import Path

from mourice.modules import DeletePathTool, ListDirTool, ReadFileTool, WriteFileTool


def _yes(_p: str) -> bool:
    return True


def _no(_p: str) -> bool:
    return False


def test_list_dir(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    out = ListDirTool().run({"path": str(tmp_path)})
    assert "a.txt" in out and "sub" in out


def test_read_file(tmp_path: Path) -> None:
    f = tmp_path / "n.txt"
    f.write_text("привет", encoding="utf-8")
    assert ReadFileTool().run({"path": str(f)}) == "привет"


def test_read_missing(tmp_path: Path) -> None:
    assert "not found" in ReadFileTool().run({"path": str(tmp_path / "no.txt")}).lower()


def test_write_new_file_free(tmp_path: Path) -> None:
    f = tmp_path / "new.txt"
    out = WriteFileTool(_no).run(
        {"path": str(f), "content": "hi"}
    )  # confirmer denies, but new file
    assert "Wrote" in out
    assert f.read_text(encoding="utf-8") == "hi"


def test_overwrite_needs_confirm(tmp_path: Path) -> None:
    f = tmp_path / "e.txt"
    f.write_text("old", encoding="utf-8")
    assert "Cancelled" in WriteFileTool(_no).run({"path": str(f), "content": "new"})
    assert f.read_text(encoding="utf-8") == "old"
    assert "Wrote" in WriteFileTool(_yes).run({"path": str(f), "content": "new"})
    assert f.read_text(encoding="utf-8") == "new"


def test_delete_needs_confirm(tmp_path: Path) -> None:
    f = tmp_path / "d.txt"
    f.write_text("x", encoding="utf-8")
    assert "Cancelled" in DeletePathTool(_no).run({"path": str(f)})
    assert f.exists()
    assert "Deleted" in DeletePathTool(_yes).run({"path": str(f)})
    assert not f.exists()


def test_delete_directory(tmp_path: Path) -> None:
    d = tmp_path / "dir"
    d.mkdir()
    (d / "inner.txt").write_text("x", encoding="utf-8")
    assert "Deleted" in DeletePathTool(_yes).run({"path": str(d)})
    assert not d.exists()
