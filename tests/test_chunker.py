"""Citation-critical guarantees: page metadata survives chunking; overlap holds."""
from __future__ import annotations

from collections import defaultdict

from app.rag.chunker import chunk_documents
from app.rag.loader import load_pdf


def test_loader_emits_one_doc_per_page_with_metadata(sample_pdf):
    docs = load_pdf(sample_pdf)
    assert len(docs) == 3
    assert [d.metadata["page"] for d in docs] == [1, 2, 3]
    assert all(d.metadata["source"] == "sample.pdf" for d in docs)
    assert all("section" in d.metadata for d in docs)


def test_every_chunk_carries_source_and_page(sample_pdf):
    chunks = chunk_documents(load_pdf(sample_pdf))
    assert chunks, "expected at least one chunk"
    for chunk in chunks:
        assert chunk.metadata["source"] == "sample.pdf"
        assert isinstance(chunk.metadata["page"], int)
        assert "section" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert chunk.page_content.strip()


def test_chunks_keep_correct_page(sample_pdf):
    chunks = chunk_documents(load_pdf(sample_pdf))
    pages = {c.metadata["page"] for c in chunks}
    assert pages <= {1, 2, 3}
    # "weighted sums" appears only in the page-1 body text.
    for chunk in chunks:
        if "weighted sums" in chunk.page_content.lower():
            assert chunk.metadata["page"] == 1


def test_chunk_index_is_contiguous_per_page(sample_pdf):
    chunks = chunk_documents(load_pdf(sample_pdf))
    indices: dict[tuple[str, int], list[int]] = defaultdict(list)
    for chunk in chunks:
        key = (chunk.metadata["source"], chunk.metadata["page"])
        indices[key].append(chunk.metadata["chunk_index"])
    for values in indices.values():
        assert values == list(range(len(values)))


def test_adjacent_chunks_overlap(long_page_pdf):
    docs = load_pdf(long_page_pdf)
    assert len(docs) == 1
    chunks = chunk_documents(docs)
    assert len(chunks) >= 2, "long page should split into multiple chunks"
    for previous, nxt in zip(chunks, chunks[1:]):
        tail = previous.page_content[-40:]
        assert tail and tail in nxt.page_content, "overlap text should carry forward"
