"""Vector store over ChromaDB.

Embeds chunks locally and persists them in ChromaDB for semantic search.
Embeddings are computed here and passed explicitly, so the store does not
depend on Chroma's embedding-function plumbing and stays easy to test.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import chromadb

from mourice.log import logger

from .chunking import Chunk

__all__ = ["ChromaStore", "Embedder"]

# Maps a list of texts to a list of embedding vectors.
Embedder = Callable[[list[str]], list[list[float]]]

_SCALAR_FRONTMATTER_KEYS = ("memory_type", "created", "as_of", "confidence", "status")


def _default_embedder() -> Embedder:
    """Local sentence-transformers embedder via Chroma's default (downloads once)."""
    from chromadb.utils import embedding_functions

    ef = embedding_functions.DefaultEmbeddingFunction()

    def embed(texts: list[str]) -> list[list[float]]:
        vectors = ef(texts)
        return [list(map(float, v)) for v in vectors]

    return embed


def _chunk_metadata(chunk: Chunk) -> dict[str, str | int | float | bool]:
    meta: dict[str, str | int | float | bool] = {
        "note_path": chunk.note_path,
        "note_title": chunk.note_title,
        "breadcrumb": chunk.breadcrumb,
        "chunk_index": chunk.index,
    }
    for key in _SCALAR_FRONTMATTER_KEYS:
        value = chunk.frontmatter.get(key)
        if isinstance(value, (str, int, float, bool)):
            meta[key] = value
        elif value is not None:
            meta[key] = str(value)
    return meta


class ChromaStore:
    """Persistent ChromaDB-backed store for note chunks."""

    def __init__(
        self,
        data_dir: str | Path,
        collection_name: str,
        *,
        embedder: Embedder | None = None,
        client: Any | None = None,
    ) -> None:
        self._client = client or chromadb.PersistentClient(path=str(data_dir))
        self._collection = self._client.get_or_create_collection(name=collection_name)
        self._embedder = embedder

    def _get_embedder(self) -> Embedder:
        if self._embedder is None:
            self._embedder = _default_embedder()
        return self._embedder

    def add_chunks(self, chunks: Iterable[Chunk]) -> int:
        """Embed and upsert chunks. Returns how many were written."""
        items = list(chunks)
        if not items:
            return 0
        embeddings = self._get_embedder()([c.text for c in items])
        self._collection.upsert(
            ids=[c.id for c in items],
            documents=[c.text for c in items],
            metadatas=[_chunk_metadata(c) for c in items],
            embeddings=embeddings,  # type: ignore[arg-type]
        )
        logger.bind(count=len(items)).info("Chunks upserted to ChromaDB")
        return len(items)

    def count(self) -> int:
        """Number of stored chunks."""
        return self._collection.count()

    def delete_by_note(self, note_path: str) -> None:
        """Delete all chunks belonging to a given note (by metadata)."""
        self._collection.delete(where={"note_path": note_path})

    def reset(self) -> None:
        """Delete and recreate the collection (used by full re-sync)."""
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(name=name)
