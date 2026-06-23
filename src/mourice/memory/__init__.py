"""Long-term memory: Obsidian vault + ChromaDB vector store (RAG)."""

from .chunking import Chunk, chunk_note, chunk_notes
from .embedders import ollama_embedder
from .store import ChromaStore, Embedder, SearchResult
from .sync import SyncResult, build_store, sync_to_store, sync_vault
from .vault import Note, VaultReader, parse_frontmatter

__all__ = [
    "ChromaStore",
    "Chunk",
    "Embedder",
    "Note",
    "SearchResult",
    "SyncResult",
    "VaultReader",
    "build_store",
    "chunk_note",
    "chunk_notes",
    "ollama_embedder",
    "parse_frontmatter",
    "sync_to_store",
    "sync_vault",
]
