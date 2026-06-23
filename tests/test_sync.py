"""Tests for incremental vault → ChromaDB sync."""

from __future__ import annotations

import uuid
from pathlib import Path

import chromadb

from mourice.memory import ChromaStore, VaultReader, sync_to_store


def _fake_embedder(texts: list[str]) -> list[list[float]]:
    return [[float(len(t) % 7)] * 8 for t in texts]


def _store() -> ChromaStore:
    client = chromadb.EphemeralClient()
    return ChromaStore("unused", f"test-{uuid.uuid4().hex}", embedder=_fake_embedder, client=client)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_initial_sync(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write(vault / "a.md", "# A\nalpha")
    _write(vault / "b.md", "# B\nbeta")
    store = _store()
    manifest = tmp_path / "manifest.json"

    result = sync_to_store(VaultReader(vault), store, manifest)

    assert result.notes_total == 2
    assert result.notes_changed == 2
    assert store.count() == 2
    assert manifest.exists()


def test_no_change_is_noop(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write(vault / "a.md", "# A\nalpha")
    store = _store()
    manifest = tmp_path / "manifest.json"

    sync_to_store(VaultReader(vault), store, manifest)
    result = sync_to_store(VaultReader(vault), store, manifest)  # second run

    assert result.notes_changed == 0
    assert result.chunks_written == 0
    assert store.count() == 1


def test_changed_note_resynced(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    note = vault / "a.md"
    _write(note, "# A\nalpha")
    store = _store()
    manifest = tmp_path / "manifest.json"
    sync_to_store(VaultReader(vault), store, manifest)

    _write(note, "# A\nalpha changed\n\n# More\nextra")
    result = sync_to_store(VaultReader(vault), store, manifest)

    assert result.notes_changed == 1


def test_removed_note_deleted(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write(vault / "a.md", "# A\nalpha")
    _write(vault / "b.md", "# B\nbeta")
    store = _store()
    manifest = tmp_path / "manifest.json"
    sync_to_store(VaultReader(vault), store, manifest)

    (vault / "b.md").unlink()
    result = sync_to_store(VaultReader(vault), store, manifest)

    assert result.notes_removed == 1
    assert store.count() == 1


def test_reset_rebuilds(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _write(vault / "a.md", "# A\nalpha")
    store = _store()
    manifest = tmp_path / "manifest.json"
    sync_to_store(VaultReader(vault), store, manifest)

    result = sync_to_store(VaultReader(vault), store, manifest, reset=True)
    assert result.notes_changed == 1  # everything re-synced after reset
