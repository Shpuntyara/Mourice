"""Ollama-backed LLM provider (local, streaming).

Talks to the Ollama REST API (``/api/chat``) over httpx with ``stream=True``,
which returns newline-delimited JSON. Keeps Mourice strictly local
(see "Приватность и локальность").
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Iterator
from typing import Any

import httpx

from mourice.log import logger

from .base import Message

__all__ = ["OllamaProvider"]


class OllamaProvider:
    """LLM provider backed by a local Ollama server."""

    def __init__(
        self,
        host: str,
        default_model: str,
        *,
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._default_model = default_model
        self._client = client or httpx.Client(base_url=host.rstrip("/"), timeout=timeout)

    def chat(self, messages: Iterable[Message], *, model: str | None = None) -> Iterator[str]:
        """Stream the assistant reply from Ollama as text chunks."""
        selected = model or self._default_model
        payload = {
            "model": selected,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        started = time.perf_counter()
        log = logger.bind(model=selected)
        log.debug("Ollama chat request")

        eval_count = 0
        with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data: dict[str, Any] = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
                if isinstance(data.get("eval_count"), int):
                    eval_count = data["eval_count"]
                if data.get("done"):
                    break

        elapsed = time.perf_counter() - started
        log.bind(latency_s=round(elapsed, 3), eval_count=eval_count).info("Ollama chat done")

    def complete(self, messages: Iterable[Message], *, model: str | None = None) -> str:
        """Return the full reply as a single string."""
        return "".join(self.chat(messages, model=model))

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> OllamaProvider:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
