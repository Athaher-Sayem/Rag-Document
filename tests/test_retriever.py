"""Retrieval behavior: source scoping and page diversity.

These require embeddings (OpenAI key) and are skipped when none is configured.
"""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.rag.chunker import chunk_documents
from app.rag.loader import load_pdf
from app.rag.retriever import retrieve
from app.rag.vectordb import add_documents, delete_by_source

_HAS_KEY = bool(get_settings().openai_api_key)
requires_key = pytest.mark.skipif(not _HAS_KEY, reason="no OpenAI API key configured")


@pytest.fixture
def indexed(sample_pdf, isolated_chroma):
    delete_by_source("sample.pdf")
    add_documents(chunk_documents(load_pdf(sample_pdf)))
    yield
    try:
        delete_by_source("sample.pdf")
    except Exception:
        pass


@requires_key
def test_retrieve_returns_tagged_chunks(indexed):
    chunks = retrieve("attention mechanism", source="sample.pdf")
    assert chunks
    for chunk in chunks:
        assert chunk.metadata["source"] == "sample.pdf"
        assert isinstance(chunk.metadata["page"], int)


@requires_key
def test_source_filter_excludes_other_documents(indexed):
    chunks = retrieve("transformers", source="sample.pdf")
    assert all(c.metadata["source"] == "sample.pdf" for c in chunks)


@requires_key
def test_mmr_returns_multiple_pages_for_broad_query(indexed):
    chunks = retrieve("attention and transformers and scaling", source="sample.pdf")
    pages = {c.metadata["page"] for c in chunks}
    assert len(pages) >= 2, "MMR should surface chunks from multiple pages"
