"""Long-term memory: Obsidian vault + ChromaDB vector store (RAG)."""

from .chunking import Chunk, chunk_note, chunk_notes
from .vault import Note, VaultReader, parse_frontmatter

__all__ = [
    "Chunk",
    "Note",
    "VaultReader",
    "chunk_note",
    "chunk_notes",
    "parse_frontmatter",
]
