"""``search_memory`` tool — semantic search over the knowledge base.

Wraps the ChromaDB store's search as a callable tool so the orchestrator can let
the LLM look things up in the user's Obsidian notes (RAG).
"""

from __future__ import annotations

from typing import Any

from mourice.memory import ChromaStore

from .base import Tool, ToolParameter

__all__ = ["SearchMemoryTool"]


class SearchMemoryTool(Tool):
    """Search the user's knowledge base for relevant notes."""

    name = "search_memory"
    description = (
        "Search the user's personal knowledge base (Obsidian notes) by meaning. "
        "Use this whenever you need facts about the user, their projects, decisions, "
        "people, or anything they may have written down."
    )
    parameters = (ToolParameter("query", "string", "What to look for, in natural language."),)

    def __init__(self, store: ChromaStore, *, n_results: int = 5) -> None:
        self._store = store
        self._n_results = n_results

    def run(self, arguments: dict[str, Any]) -> str:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return "Error: 'query' is required."

        results = self._store.search(query, n_results=self._n_results)
        if not results:
            return "No relevant notes found in the knowledge base."

        blocks: list[str] = []
        for i, r in enumerate(results, start=1):
            blocks.append(f"[{i}] {r.breadcrumb} (note: {r.note_path})\n{r.text}")
        return "\n\n---\n\n".join(blocks)
