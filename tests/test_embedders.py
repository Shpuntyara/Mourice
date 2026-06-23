"""Tests for the Ollama embedder (mocked HTTP, no server needed)."""

from __future__ import annotations

import json

import httpx

from mourice.memory import ollama_embedder


def test_ollama_embedder_returns_vectors() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    client = httpx.Client(base_url="http://test", transport=httpx.MockTransport(handler))
    embed = ollama_embedder("http://test", "bge-m3", client=client)

    vectors = embed(["hello", "world"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["model"] == "bge-m3"
    assert body["input"] == ["hello", "world"]


def test_ollama_embedder_empty() -> None:
    client = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"embeddings": []})),
    )
    embed = ollama_embedder("http://test", "bge-m3", client=client)
    assert embed([]) == []
