"""Tests for the search_memory tool."""

from __future__ import annotations

import uuid

import chromadb

from mourice.memory import ChromaStore, Chunk
from mourice.modules import SearchMemoryTool, ToolRegistry


def _keyword_embedder(texts: list[str]) -> list[list[float]]:
    return [[1.0 if "cat" in t.lower() else 0.0, 1.0 if "dog" in t.lower() else 0.0] for t in texts]


def _store_with_data() -> ChromaStore:
    client = chromadb.EphemeralClient()
    store = ChromaStore(
        "unused", f"t-{uuid.uuid4().hex}", embedder=_keyword_embedder, client=client
    )
    store.add_chunks(
        [
            Chunk("c#0", "cats are great pets", "Cats.md", "Cats", "Cats", 0, {}),
            Chunk("d#0", "dogs love to run", "Dogs.md", "Dogs", "Dogs", 0, {}),
        ]
    )
    return store


def test_finds_relevant_note() -> None:
    tool = SearchMemoryTool(_store_with_data(), n_results=1)
    result = tool.run({"query": "tell me about cats"})
    assert "Cats" in result


def test_empty_query() -> None:
    tool = SearchMemoryTool(_store_with_data())
    assert "required" in tool.run({"query": "  "}).lower()


def test_no_results() -> None:
    client = chromadb.EphemeralClient()
    empty = ChromaStore(
        "unused", f"t-{uuid.uuid4().hex}", embedder=_keyword_embedder, client=client
    )
    tool = SearchMemoryTool(empty)
    assert "no relevant notes" in tool.run({"query": "anything"}).lower()


def test_registers_and_executes() -> None:
    registry = ToolRegistry([SearchMemoryTool(_store_with_data(), n_results=1)])
    assert "search_memory" in registry
    out = registry.execute("search_memory", {"query": "dog"})
    assert "Dogs" in out
