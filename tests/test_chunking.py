"""Tests for note chunking."""

from __future__ import annotations

from pathlib import Path

from mourice.memory import Chunk, Note, chunk_note


def _note(body: str, title: str = "Test", frontmatter: dict[str, object] | None = None) -> Note:
    return Note(path=Path("Test.md"), title=title, body=body, frontmatter=frontmatter or {})


def test_chunk_by_headings() -> None:
    body = "Intro line\n\n# First\nAlpha content\n\n# Second\nBeta content"
    chunks = chunk_note(_note(body))

    assert len(chunks) == 3  # intro + two headings
    assert all(isinstance(c, Chunk) for c in chunks)
    headings = [c.breadcrumb for c in chunks]
    assert headings[1] == "Test > First"
    assert headings[2] == "Test > Second"


def test_breadcrumb_nested() -> None:
    body = "# Top\nx\n\n## Sub\ny"
    chunks = chunk_note(_note(body))
    sub = [c for c in chunks if c.breadcrumb.endswith("Sub")][0]
    assert sub.breadcrumb == "Test > Top > Sub"


def test_no_headings_single_chunk() -> None:
    chunks = chunk_note(_note("Just text, no headings."))
    assert len(chunks) == 1
    assert chunks[0].text.startswith("Test")


def test_ids_and_index_unique() -> None:
    body = "# A\n1\n\n# B\n2\n\n# C\n3"
    chunks = chunk_note(_note(body))
    ids = [c.id for c in chunks]
    assert ids == ["Test.md#0", "Test.md#1", "Test.md#2"]


def test_long_section_splits() -> None:
    big = "\n\n".join(["paragraph " * 20 for _ in range(10)])
    body = f"# Big\n{big}"
    chunks = chunk_note(_note(body), max_chars=300)
    assert len(chunks) > 1
    assert all(c.breadcrumb == "Test > Big" for c in chunks)


def test_frontmatter_carried() -> None:
    chunks = chunk_note(_note("# H\ntext", frontmatter={"memory_type": "stable"}))
    assert chunks[0].frontmatter == {"memory_type": "stable"}
