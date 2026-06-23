"""Tests for the retrieval eval harness."""

from __future__ import annotations

import uuid

import chromadb

from mourice.evals import EvalCase, evaluate
from mourice.memory import ChromaStore, Chunk


def _keyword_embedder(texts: list[str]) -> list[list[float]]:
    return [[1.0 if "cat" in t.lower() else 0.0, 1.0 if "dog" in t.lower() else 0.0] for t in texts]


def _store() -> ChromaStore:
    client = chromadb.EphemeralClient()
    store = ChromaStore("x", f"t-{uuid.uuid4().hex}", embedder=_keyword_embedder, client=client)
    store.add_chunks(
        [
            Chunk("c#0", "cats are nice", "Cats.md", "Cats", "Cats", 0, {}),
            Chunk("d#0", "dogs are loyal", "Dogs.md", "Dogs", "Dogs", 0, {}),
        ]
    )
    return store


def test_eval_hit_and_miss() -> None:
    cases = (
        EvalCase("a cat question", "Cats"),
        EvalCase("a dog question", "Nonexistent"),
    )
    report = evaluate(_store(), cases, k=1)

    assert report.total == 2
    assert report.hits == 1
    assert report.hit_rate == 0.5


def test_eval_all_hits() -> None:
    cases = (EvalCase("cat", "Cats"), EvalCase("dog", "Dogs"))
    report = evaluate(_store(), cases, k=2)
    assert report.hits == 2
    assert report.hit_rate == 1.0


def test_report_details() -> None:
    report = evaluate(_store(), (EvalCase("cat", "Cats"),), k=1)
    assert report.results[0].hit is True
    assert "Cats" in report.results[0].top
