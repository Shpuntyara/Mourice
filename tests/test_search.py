"""Tests for semantic search over the store."""

from __future__ import annotations

import uuid

import chromadb

from mourice.memory import ChromaStore, Chunk, SearchResult


def _keyword_embedder(texts: list[str]) -> list[list[float]]:
    """2-dim embedding: flags presence of 'cat' vs 'dog' (deterministic)."""
    vectors: list[list[float]] = []
    for t in texts:
        low = t.lower()
        vectors.append([1.0 if "cat" in low else 0.0, 1.0 if "dog" in low else 0.0])
    return vectors


def _chunk(cid: str, text: str, title: str) -> Chunk:
    return Chunk(
        id=cid,
        text=text,
        note_path=f"{title}.md",
        note_title=title,
        breadcrumb=title,
        index=0,
        frontmatter={},
    )


def _store() -> ChromaStore:
    client = chromadb.EphemeralClient()
    return ChromaStore(
        "unused", f"test-{uuid.uuid4().hex}", embedder=_keyword_embedder, client=client
    )


def test_search_returns_relevant() -> None:
    store = _store()
    store.add_chunks(
        [
            _chunk("c#0", "the cat sat on the mat", "Cats"),
            _chunk("d#0", "the dog ran in the park", "Dogs"),
        ]
    )
    results = store.search("tell me about a cat", n_results=1)

    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].note_title == "Cats"


def test_search_empty_collection() -> None:
    store = _store()
    assert store.search("anything") == []


def test_search_n_results() -> None:
    store = _store()
    store.add_chunks([_chunk(f"c#{i}", f"cat number {i}", f"Note{i}") for i in range(5)])
    results = store.search("cat", n_results=3)
    assert len(results) == 3
    assert all(r.distance >= 0.0 for r in results)
