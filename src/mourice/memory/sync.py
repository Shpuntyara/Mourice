"""Sync the Obsidian vault into ChromaDB.

Incremental: a manifest (JSON) maps note path -> content hash. On each run only
new/changed notes are re-embedded, and chunks of removed/changed notes are
deleted first. ``reset=True`` forces a full rebuild.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from mourice.config import Settings
from mourice.log import logger

from .chunking import chunk_note
from .store import ChromaStore
from .vault import Note, VaultReader

__all__ = ["SyncResult", "sync_to_store", "sync_vault"]


@dataclass(frozen=True)
class SyncResult:
    """Summary of a sync run."""

    notes_total: int
    notes_changed: int
    notes_removed: int
    chunks_written: int


def _note_hash(note: Note) -> str:
    payload = json.dumps(note.frontmatter, sort_keys=True, default=str) + "\n" + note.body
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Sync manifest unreadable; rebuilding from scratch")
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _save_manifest(path: Path, manifest: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_to_store(
    reader: VaultReader,
    store: ChromaStore,
    manifest_path: Path,
    *,
    reset: bool = False,
) -> SyncResult:
    """Sync notes from ``reader`` into ``store`` incrementally."""
    if reset:
        store.reset()
        manifest: dict[str, str] = {}
    else:
        manifest = _load_manifest(manifest_path)

    notes = reader.read_all()
    current = {str(note.path).replace("\\", "/"): note for note in notes}

    removed = [path for path in manifest if path not in current]
    for path in removed:
        store.delete_by_note(path)

    chunks_written = 0
    notes_changed = 0
    new_manifest: dict[str, str] = {}
    for path, note in current.items():
        digest = _note_hash(note)
        new_manifest[path] = digest
        if manifest.get(path) == digest:
            continue  # unchanged
        notes_changed += 1
        store.delete_by_note(path)  # drop stale chunks before re-adding
        chunks_written += store.add_chunks(chunk_note(note))

    _save_manifest(manifest_path, new_manifest)
    result = SyncResult(
        notes_total=len(current),
        notes_changed=notes_changed,
        notes_removed=len(removed),
        chunks_written=chunks_written,
    )
    logger.bind(
        total=result.notes_total,
        changed=result.notes_changed,
        removed=result.notes_removed,
        chunks=result.chunks_written,
    ).info("Vault synced to ChromaDB")
    return result


def sync_vault(settings: Settings, *, reset: bool = False) -> SyncResult:
    """High-level sync using application settings."""
    if not settings.obsidian_vault or not settings.chroma_dir:
        raise ValueError(
            "MOURICE_OBSIDIAN_VAULT and MOURICE_CHROMA_DIR must be set (see .env.example)"
        )
    reader = VaultReader(settings.obsidian_vault)
    store = ChromaStore(settings.chroma_dir, settings.chroma_collection)
    manifest_path = Path(settings.chroma_dir) / "sync_manifest.json"
    return sync_to_store(reader, store, manifest_path, reset=reset)
