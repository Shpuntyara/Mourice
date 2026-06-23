"""Long-term memory: Obsidian vault + ChromaDB vector store (RAG)."""

from .chunking import Chunk, chunk_note, chunk_notes
from .store import ChromaStore, Embedder
from .sync import SyncResult, sync_to_store, sync_vault
from .vault import Note, VaultReader, parse_frontmatter

__all__ = [
    "ChromaStore",
    "Chunk",
    "Embedder",
    "Note",
    "SyncResult",
    "VaultReader",
    "chunk_note",
    "chunk_notes",
    "parse_frontmatter",
    "sync_to_store",
    "sync_vault",
]
