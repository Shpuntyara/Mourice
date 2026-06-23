"""Embedding backends.

The default ChromaDB embedder (all-MiniLM-L6-v2) is English-centric, which hurts
RU/PL relevance. ``ollama_embedder`` uses a local multilingual model served by
Ollama (e.g. bge-m3) — strong on Russian and Polish, still fully local.
"""

from __future__ import annotations

import httpx

from mourice.log import logger

from .store import Embedder

__all__ = ["ollama_embedder"]


def ollama_embedder(
    host: str,
    model: str,
    *,
    timeout: float = 120.0,
    client: httpx.Client | None = None,
) -> Embedder:
    """Build an Embedder backed by Ollama's ``/api/embed`` endpoint."""
    http = client or httpx.Client(base_url=host.rstrip("/"), timeout=timeout)

    def embed(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = http.post("/api/embed", json={"model": model, "input": texts})
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Ollama /api/embed returned no embeddings")
        logger.bind(model=model, count=len(texts)).debug("Ollama embeddings computed")
        return [[float(x) for x in vec] for vec in embeddings]

    return embed
