"""Tests for the ChromaDB store using an ephemeral client + fake embedder."""

from __future__ import annotations

import uuid

import chromadb

from mourice.memory import ChromaStore, Chunk


def _fake_embedder(texts: list[str]) -> list[list[float]]:
    """Deterministic 8-dim embedding from char codes (no model download)."""
    vectors: list[list[float]] = []
    for text in texts:
        vec = [0.0] * 8
        for i, ch in enumerate(text):
            vec[i % 8] += (ord(ch) % 17) / 17.0
        vectors.append(vec)
    return vectors


def _chunk(cid: str, text: str, **fm: object) -> Chunk:
    return Chunk(
        id=cid,
        text=text,
        note_path="Note.md",
        note_title="Note",
        breadcrumb="Note > H",
        index=0,
        frontmatter=fm,
    )


def _store() -> ChromaStore:
    # Chroma clients are process-singletons, so use a unique collection per test.
    client = chromadb.EphemeralClient()
    name = f"test-{uuid.uuid4().hex}"
    return ChromaStore("unused", name, embedder=_fake_embedder, client=client)


def test_add_and_count() -> None:
    store = _store()
    written = store.add_chunks([_chunk("a#0", "hello"), _chunk("a#1", "world")])
    assert written == 2
    assert store.count() == 2


def test_add_empty() -> None:
    store = _store()
    assert store.add_chunks([]) == 0
    assert store.count() == 0


def test_upsert_is_idempotent() -> None:
    store = _store()
    store.add_chunks([_chunk("a#0", "hello")])
    store.add_chunks([_chunk("a#0", "hello updated")])  # same id
    assert store.count() == 1


def test_scalar_frontmatter_in_metadata() -> None:
    store = _store()
    store.add_chunks([_chunk("a#0", "x", memory_type="stable", tags=["drop", "me"])])
    got = store._collection.get(ids=["a#0"], include=["metadatas"])
    metadatas = got["metadatas"]
    assert metadatas is not None
    meta = metadatas[0]
    assert meta["memory_type"] == "stable"
    assert "tags" not in meta  # non-scalar dropped
    assert meta["note_title"] == "Note"


def test_reset() -> None:
    store = _store()
    store.add_chunks([_chunk("a#0", "hello")])
    store.reset()
    assert store.count() == 0
