"""Tests for the Ollama provider using a mocked HTTP transport (no server needed)."""

from __future__ import annotations

import json

import httpx

from mourice.llm import LLMProvider, Message, OllamaProvider


def _ndjson_stream(chunks: list[str]) -> bytes:
    """Build a fake Ollama /api/chat NDJSON streaming body."""
    lines = [json.dumps({"message": {"content": c}, "done": False}) for c in chunks]
    lines.append(json.dumps({"message": {"content": ""}, "done": True, "eval_count": 7}))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _make_provider(handler: httpx.MockTransport) -> OllamaProvider:
    client = httpx.Client(base_url="http://test", transport=handler)
    return OllamaProvider("http://test", "test-model", client=client)


def test_chat_streams_chunks() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, content=_ndjson_stream(["Hello", ", ", "world"]))

    provider = _make_provider(httpx.MockTransport(handler))
    chunks = list(provider.chat([Message("user", "hi")]))

    assert chunks == ["Hello", ", ", "world"]
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["stream"] is True
    assert body["model"] == "test-model"


def test_complete_joins_chunks() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_ndjson_stream(["Mou", "rice"]))

    provider = _make_provider(httpx.MockTransport(handler))
    assert provider.complete([Message("user", "name?")]) == "Mourice"


def test_model_override() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["model"] = json.loads(request.content)["model"]
        return httpx.Response(200, content=_ndjson_stream(["ok"]))

    provider = _make_provider(httpx.MockTransport(handler))
    provider.complete([Message("user", "x")], model="other-model")
    assert seen["model"] == "other-model"


def test_provider_satisfies_protocol() -> None:
    provider = _make_provider(httpx.MockTransport(lambda r: httpx.Response(200, content=b"")))
    assert isinstance(provider, LLMProvider)


def test_chat_raw_returns_message_with_tool_calls() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"function": {"name": "search_memory", "arguments": {}}}],
                }
            },
        )

    provider = _make_provider(httpx.MockTransport(handler))
    tools = [{"type": "function", "function": {"name": "search_memory"}}]
    message = provider.chat_raw([{"role": "user", "content": "hi"}], tools=tools, model="m")

    assert message["tool_calls"][0]["function"]["name"] == "search_memory"
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["stream"] is False
    assert body["tools"] == tools
